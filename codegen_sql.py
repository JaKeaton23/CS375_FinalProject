from __future__ import annotations

from typing import Optional

from .ast_nodes import ComputeNode, FilterNode, Program


SQL_AGGREGATIONS = {
    "sum": "SUM",
    "avg": "AVG",
    "count": "COUNT",
    "min": "MIN",
    "max": "MAX",
}


def generate_sql(program: Program, table_name: str = "sales") -> str:
    filters: list[FilterNode] = []
    compute: Optional[ComputeNode] = None
    for statement in program.statements:
        if isinstance(statement, FilterNode):
            filters.append(statement)
        elif isinstance(statement, ComputeNode):
            compute = statement

    if compute is None:
        return f"SELECT *\nFROM {table_name};\n"

    aggregate = SQL_AGGREGATIONS[compute.aggregation]
    where_clause = _where_clause(filters)
    return (
        f"SELECT {compute.dimension}, {aggregate}({compute.metric}) AS {compute.metric}\n"
        f"FROM {table_name}\n"
        f"{where_clause}"
        f"GROUP BY {compute.dimension}\n"
        f"ORDER BY {compute.dimension};\n"
    )


def _where_clause(filters: list[FilterNode]) -> str:
    if not filters:
        return ""
    clauses = []
    for filter_node in filters:
        pieces = []
        for index, comparison in enumerate(filter_node.condition.comparisons):
            if index > 0:
                pieces.append(filter_node.condition.logical_ops[index - 1].upper())
            pieces.append(f"{comparison.column} {comparison.operator} {_sql_literal(comparison.value)}")
        clauses.append("(" + " ".join(pieces) + ")")
    return "WHERE " + " AND ".join(clauses) + "\n"


def _sql_literal(value) -> str:
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"
