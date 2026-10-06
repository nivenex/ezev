---
name: readable-responses
description: How to format agent responses so they are quick to read and act on. Use whenever you are about to write a substantive reply that contains data, status, results, comparisons, errors, recommendations, or next steps (lookups, reports, summaries, confirmations, plans), and whenever the user asks for cleaner, clearer, or more visual output. Covers choosing the output medium (chat markdown vs terminal vs file), answer-first structure, tables for structured data, a consistent emoji/icon status legend, callouts for flags and errors, scope lines, and when to keep formatting minimal. Also covers terminal color and tables with Rich, PrettyTable, Chalk, and cli-table when the output really goes to a terminal.
---

# Readable responses

Make every reply easy to **scan in five seconds** and easy to **act on**. Good formatting is structure that carries meaning: the reader should see the answer, what needs attention, and what to do next without hunting.

## Step 1: Pick the medium (this decides the techniques)

| Where does the reply appear? | Color via ANSI codes | Tables | Icons/emoji | Use |
|---|---|---|---|---|
| **Chat UI** (claude.ai, Claude app, most agent chat panes) renders markdown | **No.** ANSI codes show as junk like `[31m` | **Markdown tables** | Yes, from a fixed legend | `references/chat-patterns.md` |
| **Real terminal / CLI program output** your code prints | Yes (Rich, Chalk) | Rich, PrettyTable, cli-table | Yes | `references/terminal-formatting.md` |
| **A file** the user will open (report, doc, spreadsheet, HTML) | Per file type | Native tables | Sparingly | The matching file skill; keep the same structure rules |
| **Plain text only** (SMS, logs, plain email) | No | Aligned monospace or lists | Optional | Lists, no markdown syntax |

If you can't tell, assume **chat markdown**. In chat, "color coding" is done with **icons and bold**, never ANSI escapes.

## Step 2: The five-second structure

Build the reply in this order, dropping any part that doesn't apply:

1. **Answer first**: one or two lines that state the result ("3 trips depart in the next 14 days; 1 needs attention").
2. **Scope line** (for data): window · basis · currency · "N of M records". Short, in italics or a subtle line.
3. **Body**: a table for structured data, bullets for options or steps, short paragraphs for explanation.
4. **Flags**: anything needing attention, grouped and visibly marked (see legend).
5. **Next step**: one concrete offer or question ("Want me to draft the follow-up task?").

Rules of thumb:
- **Lead with the conclusion**, then support it.
- **One idea per paragraph.** Aim for short paragraphs (1–3 sentences).
- **Scale formatting to the content.** A one-fact answer stays a sentence or two with no headers, tables, or icons. Formatting is for content that is genuinely multi-part, comparative, or sequential.
- Don't narrate your process ("I searched…, then I…"). Report results.
- Put the most important thing first and last; bury nothing in the middle of a wall of text.

## Step 3: Choose the right structure for the content

| Content | Use | Notes |
|---|---|---|
| Records with the same attributes (trips, bookings, payments, tasks) | **Table** | 2–6 columns, name/label first, units and currency in headers, sort by what matters (date, amount, urgency) |
| 1 record with many attributes | **Key/value list** (bold label + value) or a 2-column table | Group related fields under a short bold heading |
| Sequential actions | **Numbered list** | One action per line, verb first |
| Options or alternatives | **Short comparison table + "Top pick" line** | State why, and the trade-off |
| Status of several items | **Table with a status column using icons** | Or a list grouped by status |
| Explanation or reasoning | **Short paragraphs** | Define a term once; give one concrete example |
| Warning, error, blocker | **Callout** (blockquote with icon) | First thing the reader sees if it blocks the task |
| Large result set | **Summary table + "showing N of M"** | Offer to expand; never dump hundreds of rows |
| Code, JSON, commands | **Fenced code block** with language tag | Pretty-printed (indented) |

## Step 4: Status legend (use consistently)

Pick from this fixed set so icons always mean the same thing. Always pair an icon with a **word**, never rely on color or icon alone (accessibility, screen readers, copy/paste).

| Icon | Meaning | Use for |
|---|---|---|
| ✅ | Success / done / confirmed / paid | Completed actions, confirmed bookings |
| ⚠️ | Warning / needs attention / due soon | Upcoming deadlines, missing info, unconfirmed |
| ❌ | Error / failed / blocked / overdue | Failures, overdue items, cancelled |
| ℹ️ | Information / note / assumption | Context, scope notes, assumptions |
| 🔍 | Needs verification | Volatile facts, unverified claims |
| ⏳ | Pending / in progress / waiting | Awaiting payment, response, or approval |
| 💡 | Tip / recommendation | Suggestions, best pick |
| 📅 | Date / deadline | Key dates |
| 💰 | Money / amount | Totals, payments, commission |
| 🔒 | Sensitive / restricted | Health, passport, credentials |

Rules:
- **Max one icon per row/line**, at the start; no emoji strings, no decorative emoji in headings of formal content.
- Don't use icons for neutral rows. Absence of an icon means "nothing to flag".
- Keep the legend small; never invent new meanings for existing icons.
- Skip icons entirely for formal, client-facing, or sensitive writing (proposals, emails, legal or financial notices) unless asked.

## Step 5: Callouts

Use a blockquote with an icon and a bold label. Keep it to 1–3 lines and put blocking items first.

```
> ❌ **Couldn't complete:** the booking was rejected because the supplier payments don't add up to the fare (USD 2,400 vs 2,100). Tell me the payment schedule and I'll fix it.
```

```
> ⚠️ **Needs attention:** 2 bookings have no confirmation number.
```

```
> 🔍 **Verify before sending:** current fares and Virtuoso amenities for this sailing.
```

## Step 6: Numbers, names, and dates

- **Names, not IDs.** Show human-readable names and descriptive labels; never raw UUIDs unless asked.
- **Money:** always with a currency code or symbol and thousands separators (`CAD 12,450.00`). Right-align numeric columns. Don't mix currencies in a total without saying so.
- **Dates:** unambiguous and consistent: `Oct 9, 2026` or `2026-10-09`, not `10/9/26`. Include the weekday only when it helps. State the time zone for times.
- **Percentages and deltas:** show direction with ▲ ▼ ► only when comparing, and always with the number (`▲ 12% vs last year`).
- **Truncation:** say "showing 10 of 143" and how to see more.

## Step 7: Length and tone

- Shorter is better. Cut filler openers ("Great question!") and closers that restate the content.
- Warm and professional; match the user's register. Formatting never replaces being clear in words.
- If the reply exceeds roughly 25 lines of body, lead with a **summary**, then details, and offer to produce a document or file for the full version.
- Don't over-format: no horizontal rules between every section, no nested bullets beyond two levels, no bold for more than the few things that truly matter.

## Quick checklist before sending

1. Is the **answer** in the first two lines?
2. Is the **medium** right (markdown in chat; ANSI only in a terminal)?
3. Would a **table** make repeated data clearer, or is prose simpler?
4. Are **flags** visible and each paired with an icon **and** a word?
5. Are there **no raw IDs**, and do numbers carry units/currency and sensible rounding?
6. Is there a clear **next step**?
7. Could anything be **cut**?

## Files in this skill

| File | Use it for |
|---|---|
| `references/chat-patterns.md` | Copy-ready templates: lookup, record summary, table, comparison, report, confirmation prompt, error, no-results, partial results, and travel-agency examples |
| `references/terminal-formatting.md` | Color/table/JSON output in a real terminal with Rich, PrettyTable (Python) and Chalk, cli-table (Node); color map, `NO_COLOR`, non-TTY fallback |
| `scripts/render.py` | Turns rows (JSON/CSV) into a markdown table (stdlib only), or a Rich/ASCII terminal table; status icons; right-aligned numbers |
