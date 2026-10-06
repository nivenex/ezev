#!/usr/bin/env python3
"""
Check that this skill's references to the tripsuite-mcp skill are valid.

Usage: check_tripsuite_refs.py <path-to-tripsuite-mcp-skill-dir> [<this-skill-dir>]

Verifies:
  1. Every TripSuite tool name this skill writes in backticks (e.g. `trip_search`) exists
     in the tripsuite-mcp tool catalog.
  2. Every tripsuite-mcp file this skill points at (references/*.md) exists.
  3. Reports which operating-rule sections the tripsuite-mcp copy has (version skew).
Exit 1 if any tool name or path is wrong.
"""
import re, sys, pathlib

ts = pathlib.Path(sys.argv[1])
me = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent.parent

catalog = (ts / "references" / "tool-catalog.md").read_text()
known = set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", catalog))

PREFIX = r"(?:client|trip|booking|supplier|group|corporate_client|task|commission|statement|user|organization|destination|attachment|feedback)"
TOOL_RE = re.compile(r"`(" + PREFIX + r"_[a-z_]+)`")
# backticked snake_case words that look like tool names but are fields/enums, not tools
NOT_TOOLS = {"client_search_term"}

errors, used = [], set()
for f in list(me.rglob("*.md")):
    text = f.read_text()
    for m in TOOL_RE.finditer(text):
        name = m.group(1)
        if name in known:
            used.add(name)
        elif name not in NOT_TOOLS:
            errors.append(f"UNKNOWN TOOL `{name}` in {f.relative_to(me)}")
    for m in re.finditer(r"tripsuite-mcp[^\n]{0,80}?`?(references/[a-z\-]+\.md)`?", text):
        if not (ts / m.group(1)).exists():
            errors.append(f"MISSING FILE {m.group(1)} (referenced in {f.relative_to(me)})")

skill = (ts / "SKILL.md").read_text()
notes = []
for label, needle in [("UUID-first / confirm-after-search rule", "Resolving records"),
                      ("names-not-IDs response rule", "Showing records to the user"),
                      ("analytics caveat", "Analytics and reporting"),
                      ("workflow-patterns reference", "workflow-patterns")]:
    notes.append(f"{'OK     ' if needle in skill else 'MISSING'}  tripsuite-mcp has: {label}")

print(f"{len(used)} distinct TripSuite tool names referenced; {'all verified against the catalog' if not errors else 'see errors'}.")
for e in errors: print("ERROR ", e)
for n in notes: print(n)
sys.exit(1 if errors else 0)
