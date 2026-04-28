# BizLang

BizLang is a natural-language-inspired domain-specific language for business analytics.
It translates simple stakeholder commands into executable data analysis actions, SQL,
Pandas code, charts, CSV outputs, an AST, and a parse tree.

Example:

```text
load sales.csv
filter region = "West"
compute sum revenue by month
chart revenue by month as bar
export result as csv
```

Run the demo:

```bash
python3 -m pip install --user -r requirements.txt
PYTHONPATH=src python3 -m bizlang.cli examples/commands.biz --data-dir examples --out-dir examples/outputs
```

Run the tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Generated artifacts include:

- `ast.json`
- `parse_tree.txt`
- `generated.sql`
- `generated_pandas.py`
- `result.csv`
- `revenue_by_month.html`
- `execution_summary.txt`

Error handling demo:

```bash
PYTHONPATH=src python3 -m bizlang.cli examples/error_demo.biz --data-dir examples --out-dir examples/outputs/error_demo
```
