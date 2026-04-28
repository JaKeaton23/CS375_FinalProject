from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    DATE = auto()
    OPERATOR = auto()
    DOT = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "load",
    "filter",
    "compute",
    "by",
    "chart",
    "as",
    "export",
    "and",
    "or",
    "sum",
    "avg",
    "average",
    "count",
    "min",
    "max",
    "bar",
    "line",
    "pie",
    "result",
    "query",
    "csv",
    "json",
    "html",
    "sql",
    "python",
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._at_end:
            char = self._peek()
            if char in " \t\r":
                self._advance()
            elif char == "\n":
                tokens.append(Token(TokenType.NEWLINE, "\n", self.line, self.column))
                self._advance_line()
            elif char == "#":
                self._skip_comment()
            elif char == '"':
                tokens.append(self._string())
            elif char.isdigit():
                tokens.append(self._number_or_date())
            elif char.isalpha() or char in "_-/":
                tokens.append(self._identifier_or_keyword())
            elif char == ".":
                tokens.append(Token(TokenType.DOT, char, self.line, self.column))
                self._advance()
            elif char in "=!<>":
                tokens.append(self._operator())
            else:
                raise LexerError(f"Unexpected character {char!r} at line {self.line}, column {self.column}.")

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    @property
    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        position = self.index + offset
        if position >= len(self.source):
            return "\0"
        return self.source[position]

    def _advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        self.column += 1
        return char

    def _advance_line(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1

    def _skip_comment(self) -> None:
        while not self._at_end and self._peek() != "\n":
            self._advance()

    def _string(self) -> Token:
        start_line = self.line
        start_column = self.column
        self._advance()
        value = []
        while not self._at_end and self._peek() != '"':
            if self._peek() == "\n":
                raise LexerError(f"Unterminated string at line {start_line}, column {start_column}.")
            value.append(self._advance())
        if self._at_end:
            raise LexerError(f"Unterminated string at line {start_line}, column {start_column}.")
        self._advance()
        return Token(TokenType.STRING, "".join(value), start_line, start_column)

    def _number_or_date(self) -> Token:
        start = self.index
        start_line = self.line
        start_column = self.column
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "-" and self._peek(1).isdigit():
            while self._peek().isdigit() or self._peek() == "-":
                self._advance()
            return Token(TokenType.DATE, self.source[start:self.index], start_line, start_column)
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        return Token(TokenType.NUMBER, self.source[start:self.index], start_line, start_column)

    def _identifier_or_keyword(self) -> Token:
        start = self.index
        start_line = self.line
        start_column = self.column
        while self._peek().isalnum() or self._peek() in "_-/":
            self._advance()
        value = self.source[start:self.index]
        token_type = TokenType.KEYWORD if value.lower() in KEYWORDS else TokenType.IDENTIFIER
        return Token(token_type, value, start_line, start_column)

    def _operator(self) -> Token:
        start_line = self.line
        start_column = self.column
        char = self._advance()
        if char in "!<>" and self._peek() == "=":
            return Token(TokenType.OPERATOR, char + self._advance(), start_line, start_column)
        if char == "!":
            raise LexerError(f"Expected != at line {start_line}, column {start_column}.")
        return Token(TokenType.OPERATOR, char, start_line, start_column)

