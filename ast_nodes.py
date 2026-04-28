from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, Union


@dataclass(frozen=True)
class Comparison:
    column: str
    operator: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Condition:
    comparisons: list[Comparison]
    logical_ops: list[Literal["and", "or"]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "condition",
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "logical_ops": self.logical_ops,
        }


@dataclass(frozen=True)
class LoadNode:
    file: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": "load", "file": self.file}


@dataclass(frozen=True)
class FilterNode:
    condition: Condition

    def to_dict(self) -> dict[str, Any]:
        return {"type": "filter", "condition": self.condition.to_dict()}


@dataclass(frozen=True)
class ComputeNode:
    aggregation: str
    metric: str
    dimension: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "compute",
            "aggregation": self.aggregation,
            "metric": self.metric,
            "dimension": self.dimension,
        }


@dataclass(frozen=True)
class ChartNode:
    metric: str
    dimension: str
    chart_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "chart",
            "metric": self.metric,
            "dimension": self.dimension,
            "chart_type": self.chart_type,
        }


@dataclass(frozen=True)
class ExportNode:
    target: str
    format: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": "export", "target": self.target, "format": self.format}


Statement = Union[LoadNode, FilterNode, ComputeNode, ChartNode, ExportNode]


@dataclass(frozen=True)
class Program:
    statements: list[Statement]

    def to_dict(self) -> dict[str, Any]:
        return {"type": "program", "statements": [stmt.to_dict() for stmt in self.statements]}


def parse_tree(program: Program) -> str:
    lines = ["program"]
    for statement in program.statements:
        if isinstance(statement, LoadNode):
            lines.extend(["  load_stmt", f"    file: {statement.file}"])
        elif isinstance(statement, FilterNode):
            lines.append("  filter_stmt")
            lines.append("    condition")
            for index, comparison in enumerate(statement.condition.comparisons):
                if index > 0:
                    lines.append(f"      logical_op: {statement.condition.logical_ops[index - 1]}")
                lines.append("      comparison")
                lines.append(f"        identifier: {comparison.column}")
                lines.append(f"        comparison_op: {comparison.operator}")
                lines.append(f"        literal: {comparison.value}")
        elif isinstance(statement, ComputeNode):
            lines.extend(
                [
                    "  compute_stmt",
                    f"    aggregation: {statement.aggregation}",
                    f"    metric: {statement.metric}",
                    f"    dimension: {statement.dimension}",
                ]
            )
        elif isinstance(statement, ChartNode):
            lines.extend(
                [
                    "  chart_stmt",
                    f"    metric: {statement.metric}",
                    f"    dimension: {statement.dimension}",
                    f"    chart_type: {statement.chart_type}",
                ]
            )
        elif isinstance(statement, ExportNode):
            lines.extend(
                [
                    "  export_stmt",
                    f"    target: {statement.target}",
                    f"    export_format: {statement.format}",
                ]
            )
    return "\n".join(lines) + "\n"
