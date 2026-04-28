# BizLang: A Business Analytics Command-to-Action Language

## Team Members

Jayden Keaton

## Domain Description

BizLang is a domain-specific language for business analytics automation. Its intended users are analysts, managers, and business stakeholders who know what question they want to ask but may not want to write SQL or Python directly. The language translates short commands into an executable data-analysis pipeline.

The chosen real-world domain is business analytics. BizLang supports loading CSV data, filtering rows, computing aggregate metrics by business dimensions, generating charts, and exporting results.

## Language Objectives

BizLang was designed with four goals:

1. Use commands that resemble plain English.
2. Keep the grammar formal enough to parse predictably.
3. Produce visible real-world outputs: tables, SQL, Python, and charts.
4. Provide clear error handling for invalid commands or unknown data columns.

## User Model

The expected user understands business concepts such as revenue, region, month, product, expenses, and margin. The user is not expected to know Pandas syntax, SQL group-by syntax, or charting library APIs.

## System Assumptions

BizLang assumes input data is stored in CSV files. It assumes column names in commands match column names in the loaded dataset. It also assumes commands are written one statement per line. The language intentionally uses a constrained grammar instead of unrestricted natural language so that every valid program has a predictable interpretation.

## Design Trade-Offs

The project favors reliability over broad natural-language coverage. A fully natural-language system would require more ambiguous parsing and more inference. BizLang instead uses command phrases such as `compute sum revenue by month`, which are easy for people to read but deterministic for the parser.

## Grammar Definition

The complete grammar is provided in `grammar/bizlang.ebnf`. The main language structure is:

```ebnf
program        ::= statement+
statement      ::= load_stmt | filter_stmt | compute_stmt | chart_stmt | export_stmt
load_stmt      ::= "load" file
filter_stmt    ::= "filter" condition
compute_stmt   ::= "compute" aggregation? metric "by" dimension
chart_stmt     ::= "chart" metric "by" dimension "as" chart_type
export_stmt    ::= "export" target "as" export_format
```

## Parser Strategy

BizLang uses a recursive descent parser. This approach was chosen because the grammar is small, readable, and naturally maps to parser methods such as `load_stmt`, `filter_stmt`, `compute_stmt`, and `chart_stmt`.

The parser first receives tokens from the lexer. It then consumes tokens according to the grammar and builds AST nodes. Syntax errors include the line and column where parsing failed.

## AST Design

The AST uses one node type per major command:

- `LoadNode`
- `FilterNode`
- `ComputeNode`
- `ChartNode`
- `ExportNode`

The AST separates syntax from execution. For example, the command:

```text
compute sum revenue by month
```

becomes:

```json
{
  "type": "compute",
  "aggregation": "sum",
  "metric": "revenue",
  "dimension": "month"
}
```

## Example Run

Input file:

```text
load sales.csv
filter region = "West"
compute sum revenue by month
chart revenue by month as bar
export result as csv
export chart as html
```

Generated SQL:

```sql
SELECT month, SUM(revenue) AS revenue
FROM sales
WHERE (region = 'West')
GROUP BY month
ORDER BY month;
```

## Executable Program

The executable implementation is in `src/bizlang`. It can be run with:

```bash
python3 -m pip install --user -r requirements.txt
PYTHONPATH=src python3 -m bizlang.cli examples/commands.biz --data-dir examples --out-dir examples/outputs
```

The system produces:

- AST JSON
- Parse tree text
- SQL query
- Pandas script
- Result CSV
- Interactive Plotly chart HTML
- Execution summary

## Testing

The project includes a `unittest` suite in `tests/test_bizlang.py`. The tests verify parser output, SQL generation, successful execution/export, and semantic error handling for an unknown column.

Run tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Current result: 4 tests pass.

## Limitations

BizLang does not support joins, nested subqueries, arbitrary arithmetic expressions, or automatic synonym handling in this base version. It also does not infer column names if the user misspells them. These are reasonable future extensions.

## Future Work

The most natural extension is a Streamlit interface where users upload a CSV and type BizLang commands into a web IDE. Another extension is a synonym dictionary so phrases like `earnings`, `sales`, and `revenue` can resolve to the same column.
