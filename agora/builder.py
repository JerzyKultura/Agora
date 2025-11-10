"""Flow builder DSL for Agora workflows.

Provides a fluent interface for composing flows from registered nodes
without manual chaining.
"""

from typing import Any, Dict, Optional, Union

from .registry import _global_registry


class FlowBuilder:
    """Fluent builder for constructing AsyncFlow workflows.

    Simplifies flow creation by allowing nodes to be added by name
    and automatically chaining them together.
    """

    def __init__(self, name: str = "flow", registry=None):
        """Initialize the flow builder.

        Args:
            name: Name for the flow.
            registry: Optional custom registry (defaults to global).
        """
        self.name = name
        self.registry = registry or _global_registry
        self._nodes: list = []
        self._edges: list = []
        self._start_node = None
        self._last_node = None

    def add(
        self, node: Union[str, Any], node_name: Optional[str] = None, **params: Any
    ) -> "FlowBuilder":
        """Add a node to the flow.

        Args:
            node: Either a node class name (str) or a node instance.
            node_name: Optional custom name for the node instance.
            **params: Parameters to pass to the node constructor (if node is a string).

        Returns:
            Self for chaining.
        """
        # Create node instance if needed
        if isinstance(node, str):
            if node_name:
                params["name"] = node_name
            node_instance = self.registry.create(node, **params)
        else:
            node_instance = node

        # Set as start node if first
        if self._start_node is None:
            self._start_node = node_instance

        # Chain to previous node
        if self._last_node is not None:
            self._last_node.next(node_instance)
            self._edges.append(
                {
                    "from": self._last_node.name,
                    "to": node_instance.name,
                    "action": "default",
                }
            )

        self._nodes.append(node_instance)
        self._last_node = node_instance

        return self

    def branch(
        self,
        action: str,
        node: Union[str, Any],
        node_name: Optional[str] = None,
        **params: Any,
    ) -> "FlowBuilder":
        """Add a conditional branch from the last node.

        Args:
            action: The action string that triggers this branch.
            node: Either a node class name or instance.
            node_name: Optional custom name for the node instance.
            **params: Parameters to pass to the node constructor.

        Returns:
            Self for chaining.
        """
        if self._last_node is None:
            raise ValueError("Cannot create branch: no previous node")

        # Create node instance if needed
        if isinstance(node, str):
            if node_name:
                params["name"] = node_name
            node_instance = self.registry.create(node, **params)
        else:
            node_instance = node

        # Add conditional branch
        self._last_node.next(node_instance, action=action)
        self._edges.append(
            {
                "from": self._last_node.name,
                "to": node_instance.name,
                "action": action,
            }
        )

        self._nodes.append(node_instance)

        return self

    def then(
        self, node: Union[str, Any], node_name: Optional[str] = None, **params: Any
    ) -> "FlowBuilder":
        """Alias for add() for more readable chaining.

        Args:
            node: Either a node class name or instance.
            node_name: Optional custom name for the node instance.
            **params: Parameters to pass to the node constructor.

        Returns:
            Self for chaining.
        """
        return self.add(node, node_name=node_name, **params)

    def build(self):
        """Build and return the AsyncFlow.

        Returns:
            An AsyncFlow instance with all added nodes.
        """
        # Import here to avoid circular dependency
        from agora import AsyncFlow

        flow = AsyncFlow(name=self.name, start=self._start_node)
        return flow

    def to_dict(self) -> Dict[str, Any]:
        """Export the flow structure as a dictionary.

        Returns:
            Dictionary with nodes and edges.
        """
        return {
            "name": self.name,
            "nodes": [
                {"name": node.name, "type": node.__class__.__name__}
                for node in self._nodes
            ],
            "edges": self._edges,
        }

    def to_mermaid(self) -> str:
        """Export the flow structure as Mermaid diagram.

        Returns:
            Mermaid diagram string.
        """
        lines = ["graph TD"]
        lines.append(f"    start([{self.name}])")

        if self._start_node:
            lines.append(f"    start --> {self._start_node.name}")

        for edge in self._edges:
            action_label = (
                f"|{edge['action']}|" if edge["action"] != "default" else ""
            )
            lines.append(
                f"    {edge['from']} -->{action_label} {edge['to']}"
            )

        return "\n".join(lines)
