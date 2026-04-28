from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px

from .ast_nodes import ChartNode, ComputeNode, ExportNode, FilterNode, LoadNode, Program

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class ExecutionError(Exception):
    pass


@dataclass
class ExecutionResult:
    loaded_file: Path | None = None
    result_csv: Path | None = None
    result_json: Path | None = None
    chart_html: Path | None = None
    summary: list[str] = field(default_factory=list)


class Executor:
    def __init__(self, data_dir: Path, out_dir: Path) -> None:
        self.data_dir = data_dir
        self.out_dir = out_dir
        self.df: pd.DataFrame | None = None
        self.result_df: pd.DataFrame | None = None
        self.chart = None
        self.execution_result = ExecutionResult()

    def execute(self, program: Program) -> ExecutionResult:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        for statement in program.statements:
            if isinstance(statement, LoadNode):
                self._load(statement)
            elif isinstance(statement, FilterNode):
                self._filter(statement)
            elif isinstance(statement, ComputeNode):
                self._compute(statement)
            elif isinstance(statement, ChartNode):
                self._chart(statement)
            elif isinstance(statement, ExportNode):
                self._export(statement)
        return self.execution_result

    def _load(self, statement: LoadNode) -> None:
        path = self.data_dir / statement.file
        if not path.exists():
            raise ExecutionError(f"Data file not found: {path}")
        self.df = pd.read_csv(path)
        self.execution_result.loaded_file = path
        self.execution_result.summary.append(f"Loaded {len(self.df)} rows from {path.name}.")

    def _filter(self, statement: FilterNode) -> None:
        df = self._require_df()
        mask = None
        for index, comparison in enumerate(statement.condition.comparisons):
            self._require_column(df, comparison.column)
            part = self._comparison_mask(df, comparison.column, comparison.operator, comparison.value)
            if mask is None:
                mask = part
            elif statement.condition.logical_ops[index - 1] == "and":
                mask = mask & part
            else:
                mask = mask | part
        before = len(df)
        self.df = df[mask].copy() if mask is not None else df.copy()
        self.execution_result.summary.append(f"Filtered rows from {before} to {len(self.df)}.")

    def _compute(self, statement: ComputeNode) -> None:
        df = self._require_df()
        self._require_column(df, statement.metric)
        self._require_column(df, statement.dimension)
        if statement.aggregation == "count":
            result = df.groupby(statement.dimension, as_index=False)[statement.metric].count()
        else:
            method = "mean" if statement.aggregation == "avg" else statement.aggregation
            result = getattr(df.groupby(statement.dimension, as_index=False)[statement.metric], method)()
        self.result_df = self._sort_result(result, statement.dimension).reset_index(drop=True)
        self.execution_result.summary.append(
            f"Computed {statement.aggregation}({statement.metric}) grouped by {statement.dimension}."
        )

    def _chart(self, statement: ChartNode) -> None:
        source = self.result_df if self.result_df is not None else self._require_df()
        self._require_column(source, statement.metric)
        self._require_column(source, statement.dimension)
        title = f"{statement.metric.title()} by {statement.dimension.title()}"
        if statement.chart_type == "bar":
            self.chart = px.bar(source, x=statement.dimension, y=statement.metric, title=title)
        elif statement.chart_type == "line":
            self.chart = px.line(source, x=statement.dimension, y=statement.metric, title=title)
        elif statement.chart_type == "pie":
            self.chart = px.pie(source, names=statement.dimension, values=statement.metric, title=title)
        else:
            raise ExecutionError(f"Unsupported chart type: {statement.chart_type}")
        self.execution_result.summary.append(f"Prepared {statement.chart_type} chart.")

    def _export(self, statement: ExportNode) -> None:
        if statement.target == "result":
            result = self._require_result()
            if statement.format == "csv":
                path = self.out_dir / "result.csv"
                result.to_csv(path, index=False)
                self.execution_result.result_csv = path
                self.execution_result.summary.append(f"Exported result table to {path.name}.")
            elif statement.format == "json":
                path = self.out_dir / "result.json"
                result.to_json(path, orient="records", indent=2)
                self.execution_result.result_json = path
                self.execution_result.summary.append(f"Exported result table to {path.name}.")
            else:
                raise ExecutionError(f"Cannot export result as {statement.format}.")
        elif statement.target == "chart":
            if self.chart is None:
                raise ExecutionError("Cannot export chart before a chart statement runs.")
            if statement.format != "html":
                raise ExecutionError("Charts can currently be exported only as html.")
            path = self.out_dir / "revenue_by_month.html"
            self.chart.write_html(path)
            self.execution_result.chart_html = path
            self.execution_result.summary.append(f"Exported chart to {path.name}.")
        else:
            raise ExecutionError(f"Runtime export for target {statement.target!r} is handled by code generators.")

    def _comparison_mask(self, df: pd.DataFrame, column: str, operator: str, value: Any):
        series = df[column]
        coerced_value = self._coerce_value(series, value)
        if operator == "=":
            return series == coerced_value
        if operator == "!=":
            return series != coerced_value
        if operator == ">":
            return series > coerced_value
        if operator == "<":
            return series < coerced_value
        if operator == ">=":
            return series >= coerced_value
        if operator == "<=":
            return series <= coerced_value
        raise ExecutionError(f"Unsupported comparison operator: {operator}")

    def _coerce_value(self, series: pd.Series, value: Any) -> Any:
        if pd.api.types.is_numeric_dtype(series):
            return float(value) if isinstance(value, str) and "." in value else value
        return str(value)

    def _require_df(self) -> pd.DataFrame:
        if self.df is None:
            raise ExecutionError("A load statement must run before filtering, computing, or charting.")
        return self.df

    def _require_result(self) -> pd.DataFrame:
        if self.result_df is None:
            raise ExecutionError("A compute statement must run before exporting result.")
        return self.result_df

    def _require_column(self, df: pd.DataFrame, column: str) -> None:
        if column not in df.columns:
            available = ", ".join(df.columns)
            raise ExecutionError(f"Unknown column {column!r}. Available columns: {available}")

    def _sort_result(self, result: pd.DataFrame, dimension: str) -> pd.DataFrame:
        if dimension == "month" and set(result[dimension]).issubset(set(MONTH_ORDER)):
            ordered = result.copy()
            ordered[dimension] = pd.Categorical(ordered[dimension], categories=MONTH_ORDER, ordered=True)
            ordered = ordered.sort_values(dimension)
            ordered[dimension] = ordered[dimension].astype(str)
            return ordered
        return result.sort_values(dimension)
