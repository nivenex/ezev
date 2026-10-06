#!/usr/bin/env python3
"""
Render rows as a readable table.

Input : JSON array of objects (stdin or --json FILE) or --csv FILE.
Output: markdown table (default, for chat), plain ASCII table, or Rich terminal table.

Status prefixes in cell values get an icon + word:
    ok:Confirmed   warn:Due in 3 days   error:Overdue   info:Note   pending:Awaiting   verify:Check fares
    -> "✅ Confirmed", "⚠️ Due in 3 days", ...   (Rich also colors them)

Examples
    echo '[{"Trip":"Lisbon","Amount":"1000","Status":"warn:Due soon"}]' | render.py --align Amount=right
    render.py --csv data.csv --format ascii --columns Trip,Status --max-rows 10
    render.py --format rich --title "Departures" < rows.json

Stdlib only; Rich is optional (--format rich falls back to ascii if missing).
"""
import argparse, csv, json, os, sys

ICONS = {"ok": "✅", "warn": "⚠️", "error": "❌", "info": "ℹ️", "pending": "⏳", "verify": "🔍"}
STYLES = {"ok": "green", "warn": "yellow", "error": "bold red", "info": "cyan", "pending": "magenta", "verify": "yellow"}


def parse_status(value):
    """'warn:Due soon' -> ('warn', '⚠️ Due soon'); otherwise (None, str(value))."""
    s = "" if value is None else str(value)
    head, sep, rest = s.partition(":")
    if sep and head.strip().lower() in ICONS:
        kind = head.strip().lower()
        return kind, f"{ICONS[kind]} {rest.strip()}".rstrip()
    return None, s


def esc_md(text):
    return text.replace("|", "\\|").replace("\n", " ")


def load_rows(args):
    if args.csv:
        with open(args.csv, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    raw = open(args.json, encoding="utf-8").read() if args.json else sys.stdin.read()
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("data", [data])
    if not isinstance(data, list):
        raise SystemExit("input must be a JSON array of objects")
    return data


def build(rows, columns, align_map, max_rows):
    cols = columns or list(dict.fromkeys(k for r in rows for k in r.keys()))
    shown = rows[:max_rows] if max_rows else rows
    table = []
    for r in shown:
        row = []
        for c in cols:
            kind, text = parse_status(r.get(c, ""))
            row.append((kind, text))
        table.append(row)
    aligns = [align_map.get(c, "left") for c in cols]
    return cols, table, aligns, len(shown), len(rows)


def as_markdown(cols, table, aligns):
    sep = {"left": "---", "right": "---:", "center": ":---:"}
    lines = ["| " + " | ".join(esc_md(c) for c in cols) + " |",
             "|" + "|".join(sep[a] for a in aligns) + "|"]
    for row in table:
        lines.append("| " + " | ".join(esc_md(t) for _, t in row) + " |")
    return "\n".join(lines)


def as_ascii(cols, table, aligns):
    widths = [max([len(c)] + [len(row[i][1]) for row in table]) for i, c in enumerate(cols)]

    def fmt(cells, header=False):
        out = []
        for i, t in enumerate(cells):
            a = "left" if header else aligns[i]
            out.append(t.rjust(widths[i]) if a == "right" else t.center(widths[i]) if a == "center" else t.ljust(widths[i]))
        return "| " + " | ".join(out) + " |"

    rule = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    lines = [rule, fmt(cols, True), rule] + [fmt([t for _, t in row]) for row in table] + [rule]
    return "\n".join(lines)


def as_rich(cols, table, aligns, title):
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
    except ImportError:
        sys.stderr.write("rich not installed; falling back to ascii (pip install rich)\n")
        return None
    t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold")
    for c, a in zip(cols, aligns):
        t.add_column(c, justify=a)
    for row in table:
        cells = []
        for kind, text in row:
            from rich.markup import escape
            cells.append(f"[{STYLES[kind]}]{escape(text)}[/]" if kind else escape(text))
        t.add_row(*cells)
    console = Console()  # honors NO_COLOR and non-TTY
    console.print(t)
    return ""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", help="JSON file (default: stdin)")
    p.add_argument("--csv", help="CSV file")
    p.add_argument("--format", choices=["markdown", "ascii", "rich"], default="markdown")
    p.add_argument("--columns", help="comma-separated column order/subset")
    p.add_argument("--align", action="append", default=[], metavar="COL=left|right|center",
                   help="repeatable; numeric columns usually right")
    p.add_argument("--max-rows", type=int, default=0, help="show first N rows and add a 'showing N of M' note")
    p.add_argument("--title", default=None)
    a = p.parse_args()

    rows = load_rows(a)
    if not rows:
        print("ℹ️ No rows to show.")
        return
    columns = [c.strip() for c in a.columns.split(",")] if a.columns else None
    align_map = {}
    for item in a.align:
        col, _, val = item.partition("=")
        if val not in ("left", "right", "center"):
            raise SystemExit(f"bad --align {item!r}")
        align_map[col] = val
    cols, table, aligns, shown, total = build(rows, columns, align_map, a.max_rows)

    if a.format == "rich":
        out = as_rich(cols, table, aligns, a.title)
        if out is None:
            print(as_ascii(cols, table, aligns))
    elif a.format == "ascii":
        print(as_ascii(cols, table, aligns))
    else:
        print(as_markdown(cols, table, aligns))
    if shown < total:
        print(f"\nShowing {shown} of {total}.")


if __name__ == "__main__":
    main()
