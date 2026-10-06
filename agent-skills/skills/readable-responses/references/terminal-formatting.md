# Terminal formatting (when output really goes to a terminal)

Use this only when **your code prints to a terminal/CLI** (a script, a CLI tool, a log viewer). Chat UIs don't interpret ANSI color codes; for chat, use `chat-patterns.md`.

## Contents
1. [Decide first: is it a TTY?](#1-decide-first-is-it-a-tty)
2. [Color map](#2-color-map)
3. [Python: Rich](#3-python-rich)
4. [Python: PrettyTable](#4-python-prettytable)
5. [Node.js: Chalk](#5-nodejs-chalk)
6. [Node.js: cli-table](#6-nodejs-cli-table)
7. [Formatting JSON](#7-formatting-json)
8. [Accessibility and fallbacks](#8-accessibility-and-fallbacks)
9. [Helper script](#9-helper-script)

---

## 1. Decide first: is it a TTY?

| Situation | Do |
|---|---|
| Interactive terminal (stdout is a TTY) | Color + tables + icons are fine |
| Output piped to a file, another program, CI log, or `NO_COLOR` is set | **Plain text**, no color codes, ASCII tables |
| Output goes into a chat message | Don't use ANSI at all; use markdown |
| Machine-readable output requested (`--json`) | Emit raw JSON only, no decoration |

Libraries handle most of this: Rich and Chalk auto-detect color support and respect `NO_COLOR`. Don't force color on (`force_terminal`, `FORCE_COLOR`) unless the user asks.

## 2. Color map

Use the same meaning everywhere, and always add a word or icon so meaning survives without color.

| Meaning | Color | Rich style | Chalk | Icon |
|---|---|---|---|---|
| Success / done | green | `green` | `chalk.green` | ✅ |
| Error / failed / overdue | red | `bold red` | `chalk.red.bold` | ❌ |
| Warning / attention | yellow | `yellow` | `chalk.yellow` | ⚠️ |
| Info / note | blue/cyan | `cyan` | `chalk.cyan` | ℹ️ |
| Pending / waiting | magenta or dim | `magenta` | `chalk.magenta` | ⏳ |
| Secondary detail | dim gray | `dim` | `chalk.gray` | |
| Headline / label | bold | `bold` | `chalk.bold` | |

Don't use more than 4–5 colors in one output. Avoid red/green as the only differentiator (color-blind readers): the words and icons carry meaning.

## 3. Python: Rich

Install: `pip install rich`

```python
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()  # auto-detects color; honors NO_COLOR

table = Table(title="Departures: next 14 days", box=box.SIMPLE_HEAVY, title_style="bold")
table.add_column("Departs", style="cyan", no_wrap=True)
table.add_column("Trip")
table.add_column("Client")
table.add_column("Amount (USD)", justify="right")
table.add_column("Status")

table.add_row("Oct 9",  "Danube River Cruise", "Smith, John", "2,400.00", "[green]✅ Confirmed[/green]")
table.add_row("Oct 12", "Lisbon Long Weekend", "Doe, Jane",   "1,000.00", "[yellow]⚠️ Final payment due[/yellow]")
table.add_row("Oct 20", "Galápagos",           "Miller, Tom", "9,800.00", "[bold red]❌ Overdue[/bold red]")
console.print(table)

console.print("[bold green]✅ Saved[/bold green] trip Lisbon – Doe")
console.print("[bold red]❌ Couldn't save:[/bold red] supplier payments don't add up to the fare")
```

Other Rich features worth using:
- `console.print_json(json_string)` or `rich.print_json(data=obj)` for indented, colored JSON.
- `from rich.panel import Panel; console.print(Panel("message", title="Needs attention", border_style="yellow"))` for callouts.
- `from rich.markdown import Markdown; console.print(Markdown(md_text))` to render markdown in the terminal.
- `from rich.syntax import Syntax; console.print(Syntax(code, "python", theme="ansi_dark"))` for highlighted code.
- `from rich.progress import track` for loops that take time.
- Escape user-supplied text that may contain `[` brackets: `from rich.markup import escape; escape(text)`.

## 4. Python: PrettyTable

Install: `pip install prettytable`. Good when you want plain ASCII tables that are safe to paste anywhere (no color dependence).

```python
from prettytable import PrettyTable

t = PrettyTable()
t.field_names = ["Departs", "Trip", "Client", "Amount (USD)", "Status"]
t.align = "l"
t.align["Amount (USD)"] = "r"
t.add_row(["Oct 9", "Danube River Cruise", "Smith, John", "2,400.00", "Confirmed"])
t.add_row(["Oct 12", "Lisbon Long Weekend", "Doe, Jane", "1,000.00", "Final payment due"])
print(t)
# Markdown output for chat/docs: from prettytable import TableStyle; t.set_style(TableStyle.MARKDOWN)
```

PrettyTable does not color by itself; wrap cell text with ANSI codes only when stdout is a TTY, or just use Rich.

## 5. Node.js: Chalk

Install: `npm install chalk` (v5 is ESM-only: `import chalk from 'chalk'`; use v4 for `require`).

```js
import chalk from 'chalk';

const ok   = (m) => console.log(chalk.green.bold('✅ Success: ') + m);
const warn = (m) => console.log(chalk.yellow.bold('⚠️  Warning: ') + m);
const fail = (m) => console.log(chalk.red.bold('❌ Error: ') + m);
const info = (m) => console.log(chalk.cyan('ℹ️  ') + m);

ok('Saved trip Lisbon – Doe');
warn('2 bookings have no confirmation number');
fail('Supplier payments do not add up to the fare');
console.log(chalk.bold.underline('Departures: next 14 days'));
console.log(chalk.gray('Oct 5–19 · active trips · 3 of 3'));
```

Chalk detects color support and respects `NO_COLOR`/`FORCE_COLOR`; it returns plain text when color is unsupported.

## 6. Node.js: cli-table

Install: `npm install cli-table3` (maintained fork of `cli-table`).

```js
import Table from 'cli-table3';
import chalk from 'chalk';

const table = new Table({
  head: ['Departs', 'Trip', 'Client', 'Amount (USD)', 'Status'].map((h) => chalk.bold(h)),
  colAligns: ['left', 'left', 'left', 'right', 'left'],
  style: { head: [], border: [] },   // let chalk control color
});
table.push(
  ['Oct 9',  'Danube River Cruise', 'Smith, John', '2,400.00', chalk.green('✅ Confirmed')],
  ['Oct 12', 'Lisbon Long Weekend', 'Doe, Jane',   '1,000.00', chalk.yellow('⚠️  Final payment due')],
);
console.log(table.toString());
```

## 7. Formatting JSON

| Tool | Command |
|---|---|
| Python, Rich | `from rich import print_json; print_json(data=obj)` (indented + colored) |
| Python, plain | `print(json.dumps(obj, indent=2, ensure_ascii=False))` |
| Node, plain | `console.log(JSON.stringify(obj, null, 2))` |
| Node, colored | `console.log(util.inspect(obj, { colors: true, depth: null }))` |
| Shell | `jq .` (add `-C` to force color) |

Summarize large JSON (key fields, counts) rather than printing all of it.

## 8. Accessibility and fallbacks

- **Never rely on color alone**: pair with an icon and a word.
- Respect **`NO_COLOR`** and non-TTY output; don't strip it by hand if the library already does.
- **Width:** assume 80 columns; let Rich/cli-table wrap, or shorten columns. Avoid tables wider than the terminal.
- **Emoji width** can misalign tables in some terminals; if alignment matters, use text labels (`OK`, `WARN`, `ERR`) instead of emoji.
- **Unicode box characters** can break in legacy terminals; use `box.ASCII` (Rich) or `chars` options in cli-table when output must be portable.
- Keep **machine output separate**: human formatting to stderr/stdout by default, raw data only with an explicit flag (`--json`, `--plain`).

## 9. Helper script

`scripts/render.py` renders rows to a markdown table (default), a Rich terminal table (`--format rich`, if Rich is installed), or a plain ASCII table (`--format ascii`). It is for quick consistent output, not a required dependency.

```bash
echo '[{"Trip":"Lisbon","Amount":"1000","Status":"warn:Final payment due"}]' \
  | python3 scripts/render.py --align Amount=right
python3 scripts/render.py --format ascii --csv data.csv
```

Cells written as `ok:`, `warn:`, `error:`, `info:`, `pending:`, `verify:` get the matching icon (and color in Rich).
