"""Event-driven engine for Agora workflows.

Executes AsyncFlow with automatic tracing, retries, and error handling.
Inspired by the Strands SDK event loop pattern.
"""

import asyncio
import copy
from typing import Any, Dict, Optional

from .tracer import Tracer


class EventEngine:
    """Event-driven execution engine for AsyncFlow workflows.

    Provides:
    - Automatic tracing and metrics
    - Retry logic with exponential backoff
    - Graceful error handling
    - Recursive flow execution (Strands-style)
    """

    def __init__(
        self,
        tracer: Optional[Tracer] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_cycles: int = 100,
    ):
        """Initialize the event engine.

        Args:
            tracer: Optional tracer for metrics and logging.
            max_retries: Maximum retries for failed nodes.
            retry_delay: Initial delay between retries (exponential backoff).
            max_cycles: Maximum number of flow cycles (prevents infinite loops).
        """
        self.tracer = tracer or Tracer(enable_console=True)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_cycles = max_cycles

    async def run_flow(
        self, flow, shared: Dict[str, Any], context: Optional[Any] = None, **kwargs: Any
    ) -> tuple:
        """Run an AsyncFlow with full tracing and error handling.

        Args:
            flow: The AsyncFlow instance to execute.
            shared: Shared state dictionary passed between nodes.
            context: Optional context object.
            **kwargs: Additional arguments for flow execution.

        Returns:
            Tuple of (last_action, metrics).
        """
        # Start flow trace
        self.tracer.start_flow_trace(flow.name, **kwargs)

        try:
            # Execute the flow with cycle counting
            last_action = await self._run_flow_cycle(
                flow=flow, shared=shared, context=context, cycle_count=0, **kwargs
            )

            # Mark as successful
            self.tracer.end_flow_trace(status="success")
            metrics = self.tracer.emit_metrics()

            return last_action, metrics

        except Exception as e:
            # Handle flow-level errors
            self.tracer.end_flow_trace(status="error", error=str(e))
            self.tracer.emit_metrics()
            raise

    async def _run_flow_cycle(
        self,
        flow,
        shared: Dict[str, Any],
        context: Optional[Any],
        cycle_count: int,
        **kwargs: Any,
    ) -> Optional[str]:
        """Execute a single flow cycle (internal).

        This implements the Strands-style recursive pattern where tool_use
        results in another cycle. In Agora, we recursively process nodes
        until there are no more successors.

        Args:
            flow: The AsyncFlow instance.
            shared: Shared state dictionary.
            context: Optional context.
            cycle_count: Current cycle number (for max_cycles check).
            **kwargs: Additional arguments.

        Returns:
            The last action string returned by the flow.
        """
        # Check cycle limit
        if cycle_count >= self.max_cycles:
            raise RuntimeError(f"Flow exceeded maximum cycles ({self.max_cycles})")

        # Execute flow prep
        await flow.before_run_async(shared)
        prep_result = await flow.prep_async(shared)

        # Run the orchestration
        last_action = await self._orchestrate(
            flow=flow,
            shared=shared,
            context=context,
            params=prep_result or {**flow.params},
            **kwargs,
        )

        # Execute flow post
        result = await flow.post_async(shared, prep_result, last_action)
        await flow.after_run_async(shared)

        # Check if we should recurse (simulate tool_use recursion)
        if shared.get("_recurse_flow", False):
            shared["_recurse_flow"] = False
            return await self._run_flow_cycle(
                flow=flow,
                shared=shared,
                context=context,
                cycle_count=cycle_count + 1,
                **kwargs,
            )

        return result if result is not None else last_action

    async def _orchestrate(
        self,
        flow,
        shared: Dict[str, Any],
        context: Optional[Any],
        params: Dict[str, Any],
        **kwargs: Any,
    ) -> Optional[str]:
        """Orchestrate node execution within a flow.

        Args:
            flow: The AsyncFlow instance.
            shared: Shared state dictionary.
            context: Optional context.
            params: Parameters for node execution.
            **kwargs: Additional arguments.

        Returns:
            The last action string.
        """
        curr = copy.copy(flow.start_node)
        last_action = None

        while curr:
            # Set context and params
            curr.context = context
            curr.set_params(params)

            # Execute node with tracing and retry logic
            last_action = await self._run_node_with_retry(curr, shared)

            # Get next node based on action
            curr = copy.copy(flow.get_next_node(curr, last_action))

        return last_action

    async def _run_node_with_retry(
        self, node, shared: Dict[str, Any]
    ) -> Optional[str]:
        """Run a node with retry logic and tracing.

        Args:
            node: The node instance to execute.
            shared: Shared state dictionary.

        Returns:
            The action string returned by the node.
        """
        retry_count = 0
        current_delay = self.retry_delay

        while retry_count <= self.max_retries:
            try:
                # Start node span
                with self.tracer.start_node_span(
                    node_name=node.name,
                    node_type=node.__class__.__name__,
                    retry=retry_count,
                ) as span:
                    # Execute the node
                    result = await node._run_async(shared)

                    # End span successfully
                    self.tracer.end_node_span(span, action=result)

                    return result

            except Exception as e:
                retry_count += 1

                if retry_count > self.max_retries:
                    # Max retries exceeded - handle with on_error_async
                    try:
                        result = await node.on_error_async(e, shared)
                        return result
                    except Exception:
                        # Re-raise if error handler fails
                        raise

                # Wait before retry (exponential backoff)
                await asyncio.sleep(current_delay)
                current_delay *= 2

    async def run_node(
        self, node, shared: Dict[str, Any], context: Optional[Any] = None
    ) -> Any:
        """Run a single node (without full flow orchestration).

        Useful for testing individual nodes.

        Args:
            node: The node instance to execute.
            shared: Shared state dictionary.
            context: Optional context.

        Returns:
            The result from the node.
        """
        node.context = context

        with self.tracer.start_node_span(
            node_name=node.name, node_type=node.__class__.__name__
        ) as span:
            result = await node._run_async(shared)
            self.tracer.end_node_span(span, action=result)
            return result
