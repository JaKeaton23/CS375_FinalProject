from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ast_nodes import parse_tree
from .codegen_pandas import generate_pandas
from .codegen_sql import generate_sql
from .executor import ExecutionError, Executor
from .lexer import LexerError
from .parser import Parser, ParserError


def compile_and_run(command_file: Path, data_dir: Path, out_dir: Path) -> None:
    source = command_file.read_text(encoding="utf-8")
    program = Parser.from_source(source).parse()
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "ast.json").write_text(json.dumps(program.to_dict(), indent=2), encoding="utf-8")
    (out_dir / "parse_tree.txt").write_text(parse_tree(program), encoding="utf-8")
    (out_dir / "generated.sql").write_text(generate_sql(program), encoding="utf-8")
    (out_dir / "generated_pandas.py").write_text(generate_pandas(program), encoding="utf-8")

    result = Executor(data_dir=data_dir, out_dir=out_dir).execute(program)
    (out_dir / "execution_summary.txt").write_text("\n".join(result.summary) + "\n", encoding="utf-8")

    print("BizLang compilation and execution complete.")
    print(f"AST: {out_dir / 'ast.json'}")
    print(f"Parse tree: {out_dir / 'parse_tree.txt'}")
    print(f"SQL: {out_dir / 'generated.sql'}")
    print(f"Pandas: {out_dir / 'generated_pandas.py'}")
    if result.result_csv:
        print(f"Result CSV: {result.result_csv}")
    if result.chart_html:
        print(f"Chart HTML: {result.chart_html}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and execute BizLang commands.")
    parser.add_argument("command_file", type=Path, help="Path to a .biz command file.")
    parser.add_argument("--data-dir", type=Path, default=Path("examples"), help="Directory containing CSV inputs.")
    parser.add_argument("--out-dir", type=Path, default=Path("examples/outputs"), help="Directory for generated outputs.")
    args = parser.parse_args()
    try:
        compile_and_run(args.command_file, args.data_dir, args.out_dir)
    except (LexerError, ParserError, ExecutionError) as exc:
        print(f"BizLang error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
