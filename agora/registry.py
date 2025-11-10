"""Node registry for Agora workflows.

Provides decorator-based registration and lookup for custom node classes.
Enables dynamic node instantiation by name for flow building.
"""

from typing import Any, Dict, Optional, Type


class NodeRegistry:
    """Registry for managing custom node classes.

    Allows nodes to be registered by name and retrieved for dynamic
    flow building.
    """

    def __init__(self):
        """Initialize the registry."""
        self._nodes: Dict[str, Type[Any]] = {}

    def register(
        self, node_class: Type[Any], name: Optional[str] = None
    ) -> Type[Any]:
        """Register a node class.

        Args:
            node_class: The node class to register.
            name: Optional name for the node (defaults to class name).

        Returns:
            The node class (for use as a decorator).
        """
        node_name = name or node_class.__name__

        if node_name in self._nodes:
            raise ValueError(f"Node '{node_name}' is already registered")

        self._nodes[node_name] = node_class
        return node_class

    def get(self, name: str) -> Type[Any]:
        """Get a registered node class by name.

        Args:
            name: The name of the node class.

        Returns:
            The node class.

        Raises:
            KeyError: If the node is not registered.
        """
        if name not in self._nodes:
            raise KeyError(
                f"Node '{name}' is not registered. "
                f"Available: {list(self._nodes.keys())}"
            )

        return self._nodes[name]

    def create(self, class_name: str, **kwargs: Any) -> Any:
        """Create an instance of a registered node.

        Args:
            class_name: The name of the node class.
            **kwargs: Arguments to pass to the node constructor.

        Returns:
            An instance of the node.
        """
        node_class = self.get(class_name)
        return node_class(**kwargs)

    def list_nodes(self) -> list:
        """Get a list of all registered node names."""
        return list(self._nodes.keys())

    def clear(self) -> None:
        """Clear all registered nodes."""
        self._nodes.clear()


# Global registry instance
_global_registry = NodeRegistry()


def register_node(
    node_class: Optional[Type[Any]] = None, name: Optional[str] = None
):
    """Decorator to register a node class with the global registry.

    Usage:
        @register_node
        class MyNode(AsyncNode):
            ...

        # Or with custom name:
        @register_node(name="custom_name")
        class MyNode(AsyncNode):
            ...

    Args:
        node_class: The node class (when used without arguments).
        name: Optional custom name for the node.

    Returns:
        The decorator function or the decorated class.
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        _global_registry.register(cls, name)
        return cls

    # Handle both @register_node and @register_node(name="...")
    if node_class is not None:
        return decorator(node_class)
    return decorator


def get_node(name: str) -> Type[Any]:
    """Get a node class from the global registry.

    Args:
        name: The name of the node class.

    Returns:
        The node class.
    """
    return _global_registry.get(name)


def create_node(class_name: str, **kwargs: Any) -> Any:
    """Create a node instance from the global registry.

    Args:
        class_name: The name of the node class.
        **kwargs: Arguments to pass to the node constructor.

    Returns:
        An instance of the node.
    """
    return _global_registry.create(class_name, **kwargs)


def list_registered_nodes() -> list:
    """Get a list of all registered node names."""
    return _global_registry.list_nodes()


def get_registry() -> NodeRegistry:
    """Get the global node registry instance."""
    return _global_registry
