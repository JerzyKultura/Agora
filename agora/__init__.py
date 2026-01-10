import warnings, copy, time, uuid, json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ======================================================================
# SYNC CORE CLASSES
# ======================================================================

class BaseNode:
    def __init__(self, name=None):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None

        logger.debug(f"[BaseNode.__init__] Creating node: name={self.name}, class={self.__class__.__name__}")

        # Capture source code for visualization
        try:
            import inspect
            self.code = inspect.getsource(self.__class__)
            logger.debug(f"[BaseNode.__init__] Captured source code for node: {self.name}")
        except Exception as e:
            self.code = None
            logger.debug(f"[BaseNode.__init__] Could not capture source code for {self.name}: {e}")
    
    def set_params(self, params):
        logger.debug(f"[BaseNode.set_params] Node {self.name}: Setting params={params}")
        self.params = params

    def next(self, node, action="default"):
        logger.debug(f"[BaseNode.next] Node {self.name}: Adding successor for action='{action}' -> {node.name}")
        if action in self.successors:
            logger.warning(f"[BaseNode.next] Node {self.name}: Overwriting existing successor for action='{action}' (was: {self.successors[action].name}, now: {node.name})")
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        logger.info(f"[BaseNode.next] Node {self.name}: Successor registered: action='{action}' -> {node.name}")
        return node
    
    def prep(self, shared): pass
    
    def exec(self, prep_res):
        """Override this method in subclasses to implement node logic."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.exec() must be overridden. "
            f"BaseNode.exec() is abstract and cannot be used directly."
        )
    
    def post(self, shared, prep_res, exec_res): pass

    def before_run(self, shared): pass
    def after_run(self, shared): pass

    def on_error(self, exc, shared):
        """Hook called when an error occurs"""
        logger.error(f"[BaseNode.on_error] Node {self.name}: Error handler called: {type(exc).__name__}: {exc}")
        raise exc

    def _exec(self, prep_res):
        logger.debug(f"[BaseNode._exec] Node {self.name}: Starting exec phase with prep_result type={type(prep_res).__name__}")
        try:
            result = self.exec(prep_res)
            # Check if exec() was not overridden (returns None from base implementation)
            # We check if the method is the exact same object as BaseNode.exec
            if result is None and type(self).exec is BaseNode.exec:
                logger.error(f"[BaseNode._exec] Node {self.name}: exec() not implemented - returned None")
                raise NotImplementedError(
                    f"{self.__class__.__name__}.exec() returned None. "
                    f"Did you forget to override exec()? "
                    f"All nodes must implement exec() method."
                )
            logger.debug(f"[BaseNode._exec] Node {self.name}: exec completed successfully, result type={type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"[BaseNode._exec] Node {self.name}: exec failed: {type(e).__name__}: {e}")
            raise

    def _run(self, shared):
        logger.info(f"[BaseNode._run] Node {self.name}: === NODE EXECUTION START ===")
        logger.debug(f"[BaseNode._run] Node {self.name}: Shared state keys: {list(shared.keys())}")

        self.before_run(shared)
        logger.debug(f"[BaseNode._run] Node {self.name}: before_run completed")

        try:
            logger.debug(f"[BaseNode._run] Node {self.name}: Starting prep phase")
            p = self.prep(shared)
            logger.debug(f"[BaseNode._run] Node {self.name}: prep completed, result type={type(p).__name__}")

            logger.debug(f"[BaseNode._run] Node {self.name}: Starting exec phase")
            e = self._exec(p)
            logger.debug(f"[BaseNode._run] Node {self.name}: exec completed, result type={type(e).__name__}")

            logger.debug(f"[BaseNode._run] Node {self.name}: Starting post phase")
            result = self.post(shared, p, e)
            logger.debug(f"[BaseNode._run] Node {self.name}: post completed, result={result}")

            self.after_run(shared)
            logger.debug(f"[BaseNode._run] Node {self.name}: after_run completed")

            logger.info(f"[BaseNode._run] Node {self.name}: === NODE EXECUTION SUCCESS === (result={result})")
            return result
        except Exception as exc:
            logger.error(f"[BaseNode._run] Node {self.name}: === NODE EXECUTION FAILED === Exception: {type(exc).__name__}: {exc}")
            logger.debug(f"[BaseNode._run] Node {self.name}: Invoking on_error handler")
            return self.on_error(exc, shared)
    
    def run(self, shared, context=None):
        logger.info(f"[BaseNode.run] Node {self.name}: Public run() called, context={context}")
        self.context = context
        if self.successors:
            logger.warning(f"[BaseNode.run] Node {self.name}: Has successors but running standalone - successors will be ignored. Use Flow to orchestrate.")
            warnings.warn("Node won't run successors. Use Flow.")
        result = self._run(shared)
        logger.info(f"[BaseNode.run] Node {self.name}: Run completed with result={result}")
        return result
    
    def __rshift__(self, other): return self.next(other)
    def __sub__(self, action):
        if isinstance(action, str): 
            return _ConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class _ConditionalTransition:
    """Internal helper for conditional transitions (node - 'action' >> next_node)"""
    def __init__(self, src, action): 
        self.src, self.action = src, action
    def __rshift__(self, tgt): return self.src.next(tgt, self.action)


class Node(BaseNode):
    def __init__(self, name=None, max_retries=1, wait=0):
        super().__init__(name)
        self.max_retries, self.wait = max_retries, wait
        logger.debug(f"[Node.__init__] Node {self.name}: Configured with max_retries={max_retries}, wait={wait}s")

    def exec_fallback(self, prep_res, exc):
        logger.warning(f"[Node.exec_fallback] Node {self.name}: Fallback handler called after all retries exhausted. Exception: {type(exc).__name__}: {exc}")
        raise exc

    def _exec(self, prep_res):
        logger.debug(f"[Node._exec] Node {self.name}: Starting exec with retry logic (max_retries={self.max_retries})")
        for self.cur_retry in range(self.max_retries):
            try:
                logger.debug(f"[Node._exec] Node {self.name}: Retry attempt {self.cur_retry + 1}/{self.max_retries}")
                result = self.exec(prep_res)
                # Same check as BaseNode, but after successful execution
                if result is None and type(self).exec is BaseNode.exec:
                    logger.error(f"[Node._exec] Node {self.name}: exec() not implemented - returned None")
                    raise NotImplementedError(
                        f"{self.__class__.__name__}.exec() returned None. "
                        f"Did you forget to override exec()? "
                        f"All nodes must implement exec() method."
                    )
                logger.info(f"[Node._exec] Node {self.name}: Execution succeeded on attempt {self.cur_retry + 1}/{self.max_retries}")
                return result
            except Exception as e:
                logger.warning(f"[Node._exec] Node {self.name}: Attempt {self.cur_retry + 1}/{self.max_retries} failed: {type(e).__name__}: {e}")
                if self.cur_retry == self.max_retries - 1:
                    logger.error(f"[Node._exec] Node {self.name}: All {self.max_retries} retry attempts exhausted, calling exec_fallback")
                    return self.exec_fallback(prep_res, e)
                if self.wait > 0:
                    logger.debug(f"[Node._exec] Node {self.name}: Waiting {self.wait}s before retry {self.cur_retry + 2}/{self.max_retries}")
                    time.sleep(self.wait)
                else:
                    logger.debug(f"[Node._exec] Node {self.name}: No wait configured, retrying immediately")


class BatchNode(Node):
    def _exec(self, items):
        batch_size = len(items or [])
        logger.info(f"[BatchNode._exec] Node {self.name}: Starting batch execution with {batch_size} items")
        if batch_size == 0:
            logger.warning(f"[BatchNode._exec] Node {self.name}: Empty batch provided, returning empty list")
            return []

        results = []
        for idx, item in enumerate(items):
            logger.debug(f"[BatchNode._exec] Node {self.name}: Processing batch item {idx + 1}/{batch_size}")
            result = super(BatchNode, self)._exec(item)
            results.append(result)
            logger.debug(f"[BatchNode._exec] Node {self.name}: Batch item {idx + 1}/{batch_size} completed")

        logger.info(f"[BatchNode._exec] Node {self.name}: Batch execution completed, processed {batch_size} items")
        return results


class Flow(BaseNode):
    def __init__(self, name=None, start=None):
        super().__init__(name)
        self.start_node = start
        logger.debug(f"[Flow.__init__] Flow {self.name}: Created with start_node={start.name if start else None}")

    # Flow doesn't need exec() override check since it uses _orch() instead
    def exec(self, prep_res):
        pass

    def start(self, start):
        logger.info(f"[Flow.start] Flow {self.name}: Setting start node to {start.name}")
        self.start_node = start
        return start

    def get_next_node(self, curr, action):
        logger.debug(f"[Flow.get_next_node] Flow {self.name}: Looking for successor of {curr.name} with action='{action}'")
        logger.debug(f"[Flow.get_next_node] Flow {self.name}: Available actions from {curr.name}: {list(curr.successors.keys())}")

        nxt = curr.successors.get(action or "default")

        if nxt:
            logger.info(f"[Flow.get_next_node] Flow {self.name}: Routing decision: {curr.name} --[{action}]--> {nxt.name}")
        elif curr.successors:
            logger.warning(f"[Flow.get_next_node] Flow {self.name}: Flow ends - action '{action}' not found in available actions {list(curr.successors.keys())} from node {curr.name}")
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        else:
            logger.info(f"[Flow.get_next_node] Flow {self.name}: Flow ends naturally - node {curr.name} has no successors")

        return nxt
    
    def _orch(self, shared, params=None):
        logger.info(f"[Flow._orch] Flow {self.name}: === FLOW ORCHESTRATION START ===")
        logger.debug(f"[Flow._orch] Flow {self.name}: Starting from node={self.start_node.name}")
        logger.debug(f"[Flow._orch] Flow {self.name}: Initial shared state keys: {list(shared.keys())}")

        curr, p, last_action = copy.copy(self.start_node), (params or {**self.params}), None
        node_count = 0

        while curr:
            node_count += 1
            logger.info(f"[Flow._orch] Flow {self.name}: --- Orchestration Step {node_count}: Executing node {curr.name} ---")

            curr.context = self.context
            curr.set_params(p)

            logger.debug(f"[Flow._orch] Flow {self.name}: Executing node {curr.name}._run()")
            last_action = curr._run(shared)
            logger.info(f"[Flow._orch] Flow {self.name}: Node {curr.name} returned action='{last_action}'")

            logger.debug(f"[Flow._orch] Flow {self.name}: Shared state after {curr.name}: keys={list(shared.keys())}")

            next_node = self.get_next_node(curr, last_action)
            if next_node:
                logger.debug(f"[Flow._orch] Flow {self.name}: Transitioning: {curr.name} --[{last_action}]--> {next_node.name}")
                curr = copy.copy(next_node)
            else:
                logger.info(f"[Flow._orch] Flow {self.name}: Orchestration ending at node {curr.name} (no next node for action '{last_action}')")
                curr = None

        logger.info(f"[Flow._orch] Flow {self.name}: === FLOW ORCHESTRATION COMPLETE === (executed {node_count} nodes, final_action={last_action})")
        return last_action
    
    def _run(self, shared):
        self.before_run(shared)
        try:
            p = self.prep(shared)
            o = self._orch(shared)
            result = self.post(shared, p, o)
            self.after_run(shared)
            return result
        except Exception as exc:
            return self.on_error(exc, shared)
    
    def post(self, shared, prep_res, exec_res): return exec_res
    
    def to_dict(self):
        nodes_seen, nodes, edges = set(), [], []
        def walk(node):
            if id(node) in nodes_seen: return
            nodes_seen.add(id(node))
            nodes.append({
                "name": node.name,
                "type": node.__class__.__name__,
                "code": getattr(node, 'code', None)
            })
            for action, next_node in node.successors.items():
                edges.append({"from": node.name,"to": next_node.name,"action": action})
                walk(next_node)
        if self.start_node: walk(self.start_node)
        return {"nodes": nodes, "edges": edges}
    
    def to_mermaid(self):
        graph = self.to_dict()
        lines = ["graph TD"]
        for edge in graph["edges"]:
            action_label = f"|{edge['action']}|" if edge['action'] != 'default' else ''
            lines.append(f"    {edge['from']} -->{action_label} {edge['to']}")
        return "\n".join(lines)


# ======================================================================
# ASYNC CLASSES
# ======================================================================

class _AsyncConditionalTransition:
    """Helper for async conditional transitions"""
    def __init__(self, src, action):
        self.src, self.action = src, action
    def __rshift__(self, tgt): return self.src.next(tgt, self.action)


class AsyncNode:
    """Async version of Node with full Agora features"""

    def __init__(self, name=None, max_retries=1, wait=0):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None
        self.max_retries, self.wait = max_retries, wait

        logger.debug(f"[AsyncNode.__init__] AsyncNode {self.name}: Created with max_retries={max_retries}, wait={wait}s")

        # Capture source code for visualization
        try:
            import inspect
            self.code = inspect.getsource(self.__class__)
            logger.debug(f"[AsyncNode.__init__] AsyncNode {self.name}: Captured source code")
        except Exception as e:
            self.code = None
            logger.debug(f"[AsyncNode.__init__] AsyncNode {self.name}: Could not capture source code: {e}")
    
    def set_params(self, params):
        logger.debug(f"[AsyncNode.set_params] AsyncNode {self.name}: Setting params={params}")
        self.params = params

    def next(self, node, action="default"):
        logger.debug(f"[AsyncNode.next] AsyncNode {self.name}: Adding successor for action='{action}' -> {node.name}")
        if action in self.successors:
            logger.warning(f"[AsyncNode.next] AsyncNode {self.name}: Overwriting existing successor for action='{action}' (was: {self.successors[action].name}, now: {node.name})")
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        logger.info(f"[AsyncNode.next] AsyncNode {self.name}: Successor registered: action='{action}' -> {node.name}")
        return node

    # Async methods
    async def prep_async(self, shared): pass

    async def exec_async(self, prep_res):
        """Override this method in subclasses to implement async node logic."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.exec_async() must be overridden. "
            f"AsyncNode.exec_async() is abstract and cannot be used directly."
        )

    async def post_async(self, shared, prep_res, exec_res): pass
    async def before_run_async(self, shared): pass
    async def after_run_async(self, shared): pass

    async def on_error_async(self, exc, shared):
        logger.error(f"[AsyncNode.on_error_async] AsyncNode {self.name}: Error handler called: {type(exc).__name__}: {exc}")
        raise exc

    async def exec_fallback_async(self, prep_res, exc):
        logger.warning(f"[AsyncNode.exec_fallback_async] AsyncNode {self.name}: Fallback handler called after all retries exhausted. Exception: {type(exc).__name__}: {exc}")
        raise exc
    
    async def _exec_async(self, prep_res):
        logger.debug(f"[AsyncNode._exec_async] AsyncNode {self.name}: Starting async exec with retry logic (max_retries={self.max_retries})")
        for self.cur_retry in range(self.max_retries):
            try:
                logger.debug(f"[AsyncNode._exec_async] AsyncNode {self.name}: Retry attempt {self.cur_retry + 1}/{self.max_retries}")
                result = await self.exec_async(prep_res)
                # Check if exec_async() was not overridden
                if result is None and type(self).exec_async is AsyncNode.exec_async:
                    logger.error(f"[AsyncNode._exec_async] AsyncNode {self.name}: exec_async() not implemented - returned None")
                    raise NotImplementedError(
                        f"{self.__class__.__name__}.exec_async() returned None. "
                        f"Did you forget to override exec_async()? "
                        f"All async nodes must implement exec_async() method."
                    )
                logger.info(f"[AsyncNode._exec_async] AsyncNode {self.name}: Execution succeeded on attempt {self.cur_retry + 1}/{self.max_retries}")
                return result
            except Exception as e:
                logger.warning(f"[AsyncNode._exec_async] AsyncNode {self.name}: Attempt {self.cur_retry + 1}/{self.max_retries} failed: {type(e).__name__}: {e}")
                if self.cur_retry == self.max_retries - 1:
                    logger.error(f"[AsyncNode._exec_async] AsyncNode {self.name}: All {self.max_retries} retry attempts exhausted, calling exec_fallback_async")
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0:
                    logger.debug(f"[AsyncNode._exec_async] AsyncNode {self.name}: Waiting {self.wait}s before retry {self.cur_retry + 2}/{self.max_retries}")
                    await asyncio.sleep(self.wait)
                else:
                    logger.debug(f"[AsyncNode._exec_async] AsyncNode {self.name}: No wait configured, retrying immediately")

    async def _run_async(self, shared):
        logger.info(f"[AsyncNode._run_async] AsyncNode {self.name}: === ASYNC NODE EXECUTION START ===")
        logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: Shared state keys: {list(shared.keys())}")

        await self.before_run_async(shared)
        logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: before_run_async completed")

        try:
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: Starting prep_async phase")
            p = await self.prep_async(shared)
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: prep_async completed, result type={type(p).__name__}")

            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: Starting exec_async phase")
            e = await self._exec_async(p)
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: exec_async completed, result type={type(e).__name__}")

            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: Starting post_async phase")
            result = await self.post_async(shared, p, e)
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: post_async completed, result={result}")

            await self.after_run_async(shared)
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: after_run_async completed")

            logger.info(f"[AsyncNode._run_async] AsyncNode {self.name}: === ASYNC NODE EXECUTION SUCCESS === (result={result})")
            return result
        except Exception as exc:
            logger.error(f"[AsyncNode._run_async] AsyncNode {self.name}: === ASYNC NODE EXECUTION FAILED === Exception: {type(exc).__name__}: {exc}")
            logger.debug(f"[AsyncNode._run_async] AsyncNode {self.name}: Invoking on_error_async handler")
            return await self.on_error_async(exc, shared)

    async def run_async(self, shared, context=None):
        logger.info(f"[AsyncNode.run_async] AsyncNode {self.name}: Public run_async() called, context={context}")
        self.context = context
        if self.successors:
            logger.warning(f"[AsyncNode.run_async] AsyncNode {self.name}: Has successors but running standalone - successors will be ignored. Use AsyncFlow to orchestrate.")
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        result = await self._run_async(shared)
        logger.info(f"[AsyncNode.run_async] AsyncNode {self.name}: Run completed with result={result}")
        return result

    def __rshift__(self, other): return self.next(other)
    def __sub__(self, action):
        if isinstance(action, str):
            return _AsyncConditionalTransition(self, action)
        raise TypeError("Action must be a string")


class AsyncBatchNode(AsyncNode):
    """Async batch node - sequential processing"""
    async def _exec_async(self, items):
        batch_size = len(items or [])
        logger.info(f"[AsyncBatchNode._exec_async] AsyncNode {self.name}: Starting sequential batch execution with {batch_size} items")
        if batch_size == 0:
            logger.warning(f"[AsyncBatchNode._exec_async] AsyncNode {self.name}: Empty batch provided, returning empty list")
            return []

        results = []
        for idx, item in enumerate(items):
            logger.debug(f"[AsyncBatchNode._exec_async] AsyncNode {self.name}: Processing batch item {idx + 1}/{batch_size} sequentially")
            result = await super(AsyncBatchNode, self)._exec_async(item)
            results.append(result)
            logger.debug(f"[AsyncBatchNode._exec_async] AsyncNode {self.name}: Batch item {idx + 1}/{batch_size} completed")

        logger.info(f"[AsyncBatchNode._exec_async] AsyncNode {self.name}: Sequential batch execution completed, processed {batch_size} items")
        return results


class AsyncParallelBatchNode(AsyncNode):
    """Async parallel batch node - concurrent processing"""
    async def _exec_async(self, items):
        batch_size = len(items or [])
        logger.info(f"[AsyncParallelBatchNode._exec_async] AsyncNode {self.name}: Starting parallel batch execution with {batch_size} items")
        if not items:
            logger.warning(f"[AsyncParallelBatchNode._exec_async] AsyncNode {self.name}: Empty batch provided, returning empty list")
            return []

        async def process_item(item):
            for retry in range(self.max_retries):
                try:
                    logger.debug(f"[AsyncParallelBatchNode.process_item] AsyncNode {self.name}: Processing item (attempt {retry + 1}/{self.max_retries})")
                    result = await self.exec_async(item)
                    # Check for unimplemented exec_async
                    if result is None and type(self).exec_async is AsyncNode.exec_async:
                        logger.error(f"[AsyncParallelBatchNode.process_item] AsyncNode {self.name}: exec_async() not implemented - returned None")
                        raise NotImplementedError(
                            f"{self.__class__.__name__}.exec_async() returned None. "
                            f"Did you forget to override exec_async()?"
                        )
                    return result
                except Exception as e:
                    logger.warning(f"[AsyncParallelBatchNode.process_item] AsyncNode {self.name}: Attempt {retry + 1}/{self.max_retries} failed: {type(e).__name__}: {e}")
                    if retry == self.max_retries - 1:
                        logger.error(f"[AsyncParallelBatchNode.process_item] AsyncNode {self.name}: All retries exhausted, calling fallback")
                        return await self.exec_fallback_async(item, e)
                    if self.wait > 0:
                        logger.debug(f"[AsyncParallelBatchNode.process_item] AsyncNode {self.name}: Waiting {self.wait}s before retry")
                        await asyncio.sleep(self.wait)

        logger.debug(f"[AsyncParallelBatchNode._exec_async] AsyncNode {self.name}: Starting asyncio.gather for {batch_size} items")
        results = await asyncio.gather(*[process_item(item) for item in items])
        logger.info(f"[AsyncParallelBatchNode._exec_async] AsyncNode {self.name}: Parallel batch execution completed, processed {batch_size} items concurrently")
        return results


class AsyncFlow:
    """Async version of Flow with full Agora features"""

    def __init__(self, name=None, start=None):
        self.params, self.successors = {}, {}
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
        self.context = None
        self.start_node = start
        logger.debug(f"[AsyncFlow.__init__] AsyncFlow {self.name}: Created with start_node={start.name if start else None}")

    def start(self, start):
        logger.info(f"[AsyncFlow.start] AsyncFlow {self.name}: Setting start node to {start.name}")
        self.start_node = start
        return start

    def set_params(self, params):
        logger.debug(f"[AsyncFlow.set_params] AsyncFlow {self.name}: Setting params={params}")
        self.params = params

    def get_next_node(self, curr, action):
        logger.debug(f"[AsyncFlow.get_next_node] AsyncFlow {self.name}: Looking for successor of {curr.name} with action='{action}'")
        logger.debug(f"[AsyncFlow.get_next_node] AsyncFlow {self.name}: Available actions from {curr.name}: {list(curr.successors.keys())}")

        nxt = curr.successors.get(action or "default")

        if nxt:
            logger.info(f"[AsyncFlow.get_next_node] AsyncFlow {self.name}: Routing decision: {curr.name} --[{action}]--> {nxt.name}")
        elif curr.successors:
            logger.warning(f"[AsyncFlow.get_next_node] AsyncFlow {self.name}: Flow ends - action '{action}' not found in available actions {list(curr.successors.keys())} from node {curr.name}")
            warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        else:
            logger.info(f"[AsyncFlow.get_next_node] AsyncFlow {self.name}: Flow ends naturally - node {curr.name} has no successors")

        return nxt
    
    # Async methods
    async def prep_async(self, shared): pass
    async def post_async(self, shared, prep_res, exec_res): return exec_res
    async def before_run_async(self, shared): pass
    async def after_run_async(self, shared): pass

    async def on_error_async(self, exc, shared):
        logger.error(f"[AsyncFlow.on_error_async] AsyncFlow {self.name}: Error handler called: {type(exc).__name__}: {exc}")
        raise exc

    async def _orch_async(self, shared, params=None):
        logger.info(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: === ASYNC FLOW ORCHESTRATION START ===")
        logger.debug(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Starting from node={self.start_node.name}")
        logger.debug(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Initial shared state keys: {list(shared.keys())}")

        curr = copy.copy(self.start_node)
        p = params or {**self.params}
        last_action = None
        node_count = 0

        while curr:
            node_count += 1
            logger.info(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: --- Orchestration Step {node_count}: Executing node {curr.name} ---")

            curr.context = self.context
            curr.set_params(p)

            logger.debug(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Executing node {curr.name}._run_async()")
            last_action = await curr._run_async(shared)
            logger.info(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Node {curr.name} returned action='{last_action}'")

            logger.debug(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Shared state after {curr.name}: keys={list(shared.keys())}")

            next_node = self.get_next_node(curr, last_action)
            if next_node:
                logger.debug(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Transitioning: {curr.name} --[{last_action}]--> {next_node.name}")
                curr = copy.copy(next_node)
            else:
                logger.info(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: Orchestration ending at node {curr.name} (no next node for action '{last_action}')")
                curr = None

        logger.info(f"[AsyncFlow._orch_async] AsyncFlow {self.name}: === ASYNC FLOW ORCHESTRATION COMPLETE === (executed {node_count} nodes, final_action={last_action})")
        return last_action

    async def _run_async(self, shared):
        logger.info(f"[AsyncFlow._run_async] AsyncFlow {self.name}: === ASYNC FLOW EXECUTION START ===")
        logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Initial shared state keys: {list(shared.keys())}")

        await self.before_run_async(shared)
        logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: before_run_async completed")

        try:
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Starting prep_async phase")
            p = await self.prep_async(shared)
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: prep_async completed")

            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Starting orchestration")
            o = await self._orch_async(shared)
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Orchestration completed")

            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Starting post_async phase")
            result = await self.post_async(shared, p, o)
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: post_async completed")

            await self.after_run_async(shared)
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: after_run_async completed")

            logger.info(f"[AsyncFlow._run_async] AsyncFlow {self.name}: === ASYNC FLOW EXECUTION SUCCESS === (result={result})")
            return result
        except Exception as exc:
            logger.error(f"[AsyncFlow._run_async] AsyncFlow {self.name}: === ASYNC FLOW EXECUTION FAILED === Exception: {type(exc).__name__}: {exc}")
            logger.debug(f"[AsyncFlow._run_async] AsyncFlow {self.name}: Invoking on_error_async handler")
            return await self.on_error_async(exc, shared)
    
    async def run_async(self, shared, context=None):
        logger.info(f"[AsyncFlow.run_async] AsyncFlow {self.name}: Public run_async() called, context={context}")
        self.context = context
        if self.successors:
            logger.warning(f"[AsyncFlow.run_async] AsyncFlow {self.name}: Has successors but running standalone - successors will be ignored")
            warnings.warn("Node won't run successors. Use AsyncFlow.")
        result = await self._run_async(shared)
        logger.info(f"[AsyncFlow.run_async] AsyncFlow {self.name}: Run completed with result={result}")
        return result

    def to_dict(self):
        nodes_seen, nodes, edges = set(), [], []
        def walk(node):
            if id(node) in nodes_seen: return
            nodes_seen.add(id(node))
            nodes.append({
                "name": node.name, 
                "type": node.__class__.__name__,
                "code": getattr(node, 'code', None)
            })
            for action, next_node in node.successors.items():
                edges.append({"from": node.name, "to": next_node.name, "action": action})
                walk(next_node)
        if self.start_node: walk(self.start_node)
        return {"nodes": nodes, "edges": edges}
    
    def to_mermaid(self):
        graph = self.to_dict()
        lines = ["graph TD"]
        for edge in graph["edges"]:
            action_label = f"|{edge['action']}|" if edge['action'] != 'default' else ''
            lines.append(f"    {edge['from']} -->{action_label} {edge['to']}")
        return "\n".join(lines)


class AsyncBatchFlow(AsyncFlow):
    """Async batch flow - sequential sub-flow execution"""
    async def _orch_async(self, shared, params=None):
        items = params or shared.get("items", [])
        batch_size = len(items)
        logger.info(f"[AsyncBatchFlow._orch_async] AsyncFlow {self.name}: Starting sequential batch flow with {batch_size} items")

        results = []
        for idx, item in enumerate(items):
            logger.debug(f"[AsyncBatchFlow._orch_async] AsyncFlow {self.name}: Processing batch item {idx + 1}/{batch_size}")
            item_shared = {"item": item, **shared}
            result = await super()._orch_async(item_shared, params)
            results.append(result)
            logger.debug(f"[AsyncBatchFlow._orch_async] AsyncFlow {self.name}: Batch item {idx + 1}/{batch_size} completed")

        shared["batch_results"] = results
        logger.info(f"[AsyncBatchFlow._orch_async] AsyncFlow {self.name}: Sequential batch flow completed, processed {batch_size} items")
        return results


class AsyncParallelBatchFlow(AsyncFlow):
    """Async parallel batch flow - concurrent sub-flow execution"""
    async def _orch_async(self, shared, params=None):
        items = params or shared.get("items", [])
        batch_size = len(items)
        logger.info(f"[AsyncParallelBatchFlow._orch_async] AsyncFlow {self.name}: Starting parallel batch flow with {batch_size} items")

        async def process_item(item):
            item_shared = {"item": item, **shared}
            return await super(AsyncParallelBatchFlow, self)._orch_async(item_shared, params)

        logger.debug(f"[AsyncParallelBatchFlow._orch_async] AsyncFlow {self.name}: Starting asyncio.gather for {batch_size} items")
        results = await asyncio.gather(*[process_item(item) for item in items])
        shared["batch_results"] = results
        logger.info(f"[AsyncParallelBatchFlow._orch_async] AsyncFlow {self.name}: Parallel batch flow completed, processed {batch_size} items concurrently")
        return results


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    # Sync classes
    'BaseNode', 'Node', 'BatchNode', 'Flow',
    # Async classes  
    'AsyncNode', 'AsyncFlow', 'AsyncBatchNode', 'AsyncParallelBatchNode',
    'AsyncBatchFlow', 'AsyncParallelBatchFlow'
]
