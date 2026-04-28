from __future__ import annotations

from .ast_nodes import ChartNode, Comparison, ComputeNode, Condition, ExportNode, FilterNode, LoadNode, Program
from .lexer import Lexer, Token, TokenType


class ParserError(Exception):
    pass


AGGREGATIONS = {"sum", "avg", "average", "count", "min", "max"}
CHART_TYPES = {"bar", "line", "pie"}
EXPORT_TARGETS = {"result", "query", "chart"}
EXPORT_FORMATS = {"csv", "json", "html", "sql", "python"}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    @classmethod
    def from_source(cls, source: str) -> "Parser":
        return cls(Lexer(source).tokenize())

    def parse(self) -> Program:
        statements = []
        self._skip_newlines()
        while not self._check(TokenType.EOF):
            statements.append(self._statement())
            self._skip_newlines()
        return Program(statements)

    def _statement(self):
        if self._match_keyword("load"):
            return self._load_stmt()
        if self._match_keyword("filter"):
            return self._filter_stmt()
        if self._match_keyword("compute"):
            return self._compute_stmt()
        if self._match_keyword("chart"):
            return self._chart_stmt()
        if self._match_keyword("export"):
            return self._export_stmt()
        token = self._peek()
        raise ParserError(f"Expected a statement at line {token.line}, column {token.column}; found {token.value!r}.")

    def _load_stmt(self) -> LoadNode:
        file_parts = [self._consume_identifier_like("Expected file name after load").value]
        if self._match(TokenType.DOT):
            file_parts.append(".")
            file_parts.append(self._consume_identifier_like("Expected file extension after dot").value)
        self._consume_statement_end()
        return LoadNode("".join(file_parts))

    def _filter_stmt(self) -> FilterNode:
        comparisons = [self._comparison()]
        logical_ops = []
        while self._match_keyword("and") or self._match_keyword("or"):
            logical_ops.append(self._previous().value.lower())
            comparisons.append(self._comparison())
        self._consume_statement_end()
        return FilterNode(Condition(comparisons, logical_ops))

    def _comparison(self) -> Comparison:
        column = self._consume_identifier_like("Expected column name in filter condition").value
        operator = self._consume(TokenType.OPERATOR, "Expected comparison operator").value
        value_token = self._advance()
        if value_token.type not in {TokenType.STRING, TokenType.NUMBER, TokenType.DATE, TokenType.IDENTIFIER, TokenType.KEYWORD}:
            raise ParserError(
                f"Expected literal at line {value_token.line}, column {value_token.column}; found {value_token.value!r}."
            )
        value = self._literal_value(value_token)
        return Comparison(column, operator, value)

    def _compute_stmt(self) -> ComputeNode:
        aggregation = "sum"
        if self._check(TokenType.KEYWORD) and self._peek().value.lower() in AGGREGATIONS:
            aggregation = self._advance().value.lower()
        metric = self._consume_identifier_like("Expected metric after compute").value
        self._consume_keyword("by", "Expected 'by' in compute statement")
        dimension = self._consume_identifier_like("Expected dimension after by").value
        self._consume_statement_end()
        return ComputeNode(self._normalize_aggregation(aggregation), metric, dimension)

    def _chart_stmt(self) -> ChartNode:
        metric = self._consume_identifier_like("Expected metric after chart").value
        self._consume_keyword("by", "Expected 'by' in chart statement")
        dimension = self._consume_identifier_like("Expected dimension after by").value
        self._consume_keyword("as", "Expected 'as' in chart statement")
        chart_type = self._consume_keyword_value(CHART_TYPES, "Expected chart type: bar, line, or pie")
        self._consume_statement_end()
        return ChartNode(metric, dimension, chart_type)

    def _export_stmt(self) -> ExportNode:
        target = self._consume_keyword_value(EXPORT_TARGETS, "Expected export target: result, query, or chart")
        self._consume_keyword("as", "Expected 'as' in export statement")
        export_format = self._consume_keyword_value(EXPORT_FORMATS, "Expected export format")
        self._consume_statement_end()
        return ExportNode(target, export_format)

    def _consume_statement_end(self) -> None:
        if self._check(TokenType.EOF):
            return
        if self._match(TokenType.NEWLINE):
            return
        token = self._peek()
        raise ParserError(f"Expected end of statement at line {token.line}, column {token.column}; found {token.value!r}.")

    def _skip_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            pass

    def _consume_identifier_like(self, message: str) -> Token:
        if self._check(TokenType.IDENTIFIER) or self._check(TokenType.KEYWORD):
            return self._advance()
        token = self._peek()
        raise ParserError(f"{message} at line {token.line}, column {token.column}.")

    def _consume_keyword(self, value: str, message: str) -> Token:
        if self._check(TokenType.KEYWORD) and self._peek().value.lower() == value:
            return self._advance()
        token = self._peek()
        raise ParserError(f"{message} at line {token.line}, column {token.column}.")

    def _consume_keyword_value(self, allowed: set[str], message: str) -> str:
        token = self._consume_identifier_like(message)
        lowered = token.value.lower()
        if lowered not in allowed:
            raise ParserError(f"{message} at line {token.line}, column {token.column}; found {token.value!r}.")
        return lowered

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise ParserError(f"{message} at line {token.line}, column {token.column}.")

    def _match_keyword(self, value: str) -> bool:
        if self._check(TokenType.KEYWORD) and self._peek().value.lower() == value:
            self._advance()
            return True
        return False

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._check(TokenType.EOF):
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _literal_value(self, token: Token):
        if token.type == TokenType.NUMBER:
            return float(token.value) if "." in token.value else int(token.value)
        return token.value

    def _normalize_aggregation(self, aggregation: str) -> str:
        return "avg" if aggregation == "average" else aggregation

