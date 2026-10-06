# Oceans & Rivers Travel: agent skills bundle

Three skills that work together. Install all three.

| Skill | Role | Depends on |
|---|---|---|
| `tripsuite-mcp` | How to read and change TripSuite records correctly (IDs, etags, money, confirmations) | TripSuite MCP server |
| `oceans-rivers-travel-agent` | Agency persona, knowledge, sourcing rules, planning/analysis playbooks, Virtuoso lookup | `tripsuite-mcp`; a browser tool for virtuoso.com |
| `readable-responses` | How replies are formatted (answer first, tables, icon legend, callouts) | none |

## Contents
- `skills/<name>/`: unpacked skill folders (SKILL.md + references, scripts, assets). Use for Claude Code, plugins, git repos, or any deployment that reads skill folders. Place each folder, unchanged, in the deployment's skills directory (for example `.claude/skills/`).
- `packages/<name>.skill`: the same skills as upload packages (claude.ai / Claude Desktop "upload skill").
- `skills/readable-responses/evals/evals.json`: test prompts for that skill. Evals for the other two skills were not preserved and are not included.

## Requirements
1. **TripSuite MCP server** connected (tools named `mcp__TripSuite__*`). Tools may be deferred; the skills tell the agent to load them with a tool search.
2. **Browser tool** for Virtuoso lookups: Playwright MCP, Claude in Chrome, or the built-in browser. If none is available the agent falls back to asking the user to paste the Virtuoso page.
3. Keep the skill folder names exactly as above; the skills reference each other by name (`tripsuite-mcp`).

## After installing
- Check cross-references: `python3 skills/oceans-rivers-travel-agent/scripts/check_tripsuite_refs.py skills/tripsuite-mcp`
- Fill in `skills/oceans-rivers-travel-agent/assets/preferred-partners-template.md` as suppliers are verified on virtuoso.com.
- Open items to confirm with the agency are listed at the end of `skills/oceans-rivers-travel-agent/references/agency-profile.md` (name variants, email domain, "5 stars" rating source, Virtuoso membership-fee wording).
- Tip: for non-chat deployments (terminal agents), see `readable-responses/references/terminal-formatting.md`.
