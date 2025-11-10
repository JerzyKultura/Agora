"""Flow inspector for Agora workflows.

Provides utilities for visualizing flow structure and runtime statistics.
"""

import json
from typing import Any, Dict, Optional

from .tracer import Tracer


class FlowInspector:
    """Inspector for analyzing and visualizing Agora flows.

    Provides methods to:
    - Export flow structure (to_dict, to_mermaid)
    - Display runtime statistics
    - Generate execution reports
    """

    def __init__(self, flow, tracer: Optional[Tracer] = None):
        """Initialize the inspector.

        Args:
            flow: The Flow or AsyncFlow instance to inspect.
            tracer: Optional tracer with runtime data.
        """
        self.flow = flow
        self.tracer = tracer

    def to_dict(self) -> Dict[str, Any]:
        """Export flow structure as dictionary.

        Returns:
            Dictionary containing nodes and edges.
        """
        return self.flow.to_dict()

    def to_mermaid(self) -> str:
        """Export flow structure as Mermaid diagram.

        Returns:
            Mermaid diagram string.
        """
        return self.flow.to_mermaid()

    def get_runtime_stats(self) -> Dict[str, Any]:
        """Get runtime statistics from tracer.

        Returns:
            Dictionary with execution statistics.
        """
        if not self.tracer or not self.tracer.current_trace:
            return {"error": "No runtime data available"}

        trace = self.tracer.current_trace

        # Calculate per-node statistics
        node_stats = {}
        for span in trace.spans:
            name = span.node_name
            if name not in node_stats:
                node_stats[name] = {
                    "executions": 0,
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                    "successes": 0,
                    "errors": 0,
                    "actions": [],
                }

            node_stats[name]["executions"] += 1
            node_stats[name]["total_time_ms"] += span.duration_ms or 0

            if span.status == "success":
                node_stats[name]["successes"] += 1
            elif span.status == "error":
                node_stats[name]["errors"] += 1

            if span.action:
                node_stats[name]["actions"].append(span.action)

        # Calculate averages
        for stats in node_stats.values():
            if stats["executions"] > 0:
                stats["avg_time_ms"] = (
                    stats["total_time_ms"] / stats["executions"]
                )

        return {
            "flow_name": trace.flow_name,
            "total_duration_ms": trace.duration_ms,
            "total_nodes_executed": len(trace.spans),
            "unique_nodes": len(node_stats),
            "node_stats": node_stats,
            "status": trace.status,
        }

    def print_structure(self) -> None:
        """Print flow structure in a human-readable format."""
        graph = self.to_dict()

        print(f"\n=== Flow Structure: {self.flow.name} ===")
        print(f"\nNodes ({len(graph['nodes'])}):")
        for node in graph["nodes"]:
            print(f"  - {node['name']} ({node['type']})")

        print(f"\nEdges ({len(graph['edges'])}):")
        for edge in graph["edges"]:
            action = f" [{edge['action']}]" if edge["action"] != "default" else ""
            print(f"  - {edge['from']} → {edge['to']}{action}")

    def print_runtime_stats(self) -> None:
        """Print runtime statistics in a human-readable format."""
        stats = self.get_runtime_stats()

        if "error" in stats:
            print(f"\n{stats['error']}")
            return

        print(f"\n=== Runtime Statistics: {stats['flow_name']} ===")
        print("\nOverall:")
        print(f"  Status: {stats['status']}")
        print(f"  Total Duration: {stats['total_duration_ms']:.2f}ms")
        print(f"  Nodes Executed: {stats['total_nodes_executed']}")
        print(f"  Unique Nodes: {stats['unique_nodes']}")

        print("\nPer-Node Statistics:")
        for node_name, node_stat in stats["node_stats"].items():
            print(f"  {node_name}:")
            print(f"    Executions: {node_stat['executions']}")
            print(f"    Avg Time: {node_stat['avg_time_ms']:.2f}ms")
            print(f"    Successes: {node_stat['successes']}")
            print(f"    Errors: {node_stat['errors']}")
            if node_stat["actions"]:
                print(f"    Actions: {', '.join(node_stat['actions'])}")

    def export_report(self, filepath: str) -> None:
        """Export a complete report to JSON.

        Args:
            filepath: Path to save the JSON report.
        """
        report = {
            "structure": self.to_dict(),
            "mermaid": self.to_mermaid(),
            "runtime_stats": (
                self.get_runtime_stats() if self.tracer else None
            ),
            "trace_data": self.tracer.get_trace_data() if self.tracer else None,
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport exported to: {filepath}")

    def visualize_execution_timeline(self) -> None:
        """Print a simple ASCII timeline of node executions."""
        if not self.tracer or not self.tracer.current_trace:
            print("No runtime data available for timeline visualization")
            return

        trace = self.tracer.current_trace
        if not trace.spans:
            return

        print(f"\n=== Execution Timeline: {trace.flow_name} ===\n")

        # Find time range
        min_time = min(span.start_time for span in trace.spans)
        max_time = max(span.end_time or span.start_time for span in trace.spans)
        total_duration = (max_time - min_time) * 1000  # ms

        # Print timeline
        for span in trace.spans:
            start_offset = (
                ((span.start_time - min_time) * 1000 / total_duration) * 50
            )
            duration = (span.duration_ms or 0) / total_duration * 50

            indent = " " * int(start_offset)
            bar = "█" * max(1, int(duration))

            status_icon = "✓" if span.status == "success" else "✗"
            action_str = f" → {span.action}" if span.action else ""

            print(
                f"{span.node_name:20s} {indent}{bar} {status_icon} "
                f"({span.duration_ms:.1f}ms){action_str}"
            )

        print(f"\nTotal: {total_duration:.2f}ms")


def inspect_flow(flow, tracer: Optional[Tracer] = None) -> FlowInspector:
    """Create a FlowInspector for the given flow.

    Args:
        flow: The Flow or AsyncFlow instance.
        tracer: Optional tracer with runtime data.

    Returns:
        FlowInspector instance.
    """
    return FlowInspector(flow, tracer)
