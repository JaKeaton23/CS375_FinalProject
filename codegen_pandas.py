from __future__ import annotations

from .ast_nodes import ChartNode, ComputeNode, ExportNode, FilterNode, LoadNode, Program


def generate_pandas(program: Program) -> str:
    lines = [
        "import pandas as pd",
        "import plotly.express as px",
        "",
        "data_dir = 'examples'",
        "out_dir = 'examples/outputs'",
        "df = None",
        "result = None",
        "chart = None",
        "",
    ]
    for statement in program.statements:
        if isinstance(statement, LoadNode):
            lines.append(f"df = pd.read_csv(f'{{data_dir}}/{statement.file}')")
        elif isinstance(statement, FilterNode):
            lines.append(f"df = df[{_pandas_condition(statement)}]")
        elif isinstance(statement, ComputeNode):
            agg = "mean" if statement.aggregation == "avg" else statement.aggregation
            lines.append(
                f"result = df.groupby('{statement.dimension}', as_index=False)['{statement.metric}'].{agg}()"
            )
            if statement.dimension == "month":
                lines.append("month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']")
                lines.append("result['month'] = pd.Categorical(result['month'], categories=month_order, ordered=True)")
                lines.append("result = result.sort_values('month')")
                lines.append("result['month'] = result['month'].astype(str)")
        elif isinstance(statement, ChartNode):
            source = "result if result is not None else df"
            lines.append(
                f"chart = px.{statement.chart_type}({source}, x='{statement.dimension}', y='{statement.metric}', "
                f"title='{statement.metric.title()} by {statement.dimension.title()}')"
            )
        elif isinstance(statement, ExportNode):
            if statement.target == "result" and statement.format == "csv":
                lines.append("result.to_csv(f'{out_dir}/result.csv', index=False)")
            elif statement.target == "result" and statement.format == "json":
                lines.append("result.to_json(f'{out_dir}/result.json', orient='records', indent=2)")
            elif statement.target == "chart" and statement.format == "html":
                lines.append("chart.write_html(f'{out_dir}/chart.html')")
    return "\n".join(lines) + "\n"


def _pandas_condition(filter_node: FilterNode) -> str:
    pieces = []
    for index, comparison in enumerate(filter_node.condition.comparisons):
        if index > 0:
            op = "&" if filter_node.condition.logical_ops[index - 1] == "and" else "|"
            pieces.append(op)
        pieces.append(f"(df['{comparison.column}'] {comparison.operator} {_python_literal(comparison.value)})")
    return " ".join(pieces)


def _python_literal(value) -> str:
    return repr(value)
