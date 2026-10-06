# Chat patterns (markdown): copy-ready templates

For replies that appear in a chat UI that renders markdown. Fill with real values only; never leave placeholders in the output. Remove any part that doesn't apply.

## Contents
1. [Single answer](#1-single-answer)
2. [Lookup result: table](#2-lookup-result-table)
3. [One record, many attributes](#3-one-record-many-attributes)
4. [Status table with icons](#4-status-table-with-icons)
5. [Options comparison](#5-options-comparison)
6. [Report / summary](#6-report--summary)
7. [Confirmation prompt (before an action)](#7-confirmation-prompt-before-an-action)
8. [Action completed](#8-action-completed)
9. [Error / blocked](#9-error--blocked)
10. [No results / partial results](#10-no-results--partial-results)
11. [Disambiguation (several matches)](#11-disambiguation-several-matches)
12. [Steps / how-to](#12-steps--how-to)
13. [JSON and code](#13-json-and-code)
14. [Anti-patterns](#14-anti-patterns)

---

## 1. Single answer

No headers, no table, no icons.

> Jane Doe's next trip is **Lisbon, May 3–10, 2027**, with Maria as her advisor. Want the booking details?

## 2. Lookup result: table

```
**3 trips depart in the next 14 days** (1 needs attention)
*Oct 5–19, 2026 · active trips · 3 of 3*

| Departs | Trip | Client | Advisor | Status |
|---|---|---|---|---|
| Oct 9 | Danube River Cruise | Smith, John | Sam | ✅ Confirmed |
| Oct 12 | Lisbon Long Weekend | Doe, Jane | David | ⚠️ Final payment due Oct 8 |
| Oct 17 | Galápagos Expedition | Miller, Tom | Sam | ✅ Confirmed |

> ⚠️ **Needs attention:** Lisbon Long Weekend has a final payment due in 3 days.

Want me to create a reminder task for that?
```

Table rules: name/label in the first or second column; dates sorted ascending (or the sort the user cares about); status last; numbers right-aligned (`---:`); 6 columns max (split into two tables or drop columns if more).

## 3. One record, many attributes

```
### Jane Doe
*From TripSuite*

**Contact:** jane.doe@example.com · +1 403 555 0100
**Advisor:** Sam Spencer
**Trips:** 3 total · next: Lisbon, May 3–10, 2027

**Open items**
- ⏳ Planning fee CAD 250.00, due Oct 18
- ⚠️ Passport expires Mar 2027 (check before the trip)
```

Group fields under a few bold labels; avoid a wall of `Label: value` lines longer than about 8.

## 4. Status table with icons

```
| Item | Amount | Due | Status |
|---|---:|---|---|
| Hotel deposit | USD 1,000.00 | Oct 9 | ⏳ Pending |
| Cruise final payment | USD 8,800.00 | Nov 1 | ⚠️ Due in 27 days |
| Planning fee | CAD 250.00 | Sep 20 | ❌ Overdue by 15 days |
| Insurance | USD 320.00 | Sep 1 | ✅ Paid |
```

Order by urgency (❌ → ⚠️ → ⏳ → ✅) when the point is "what should I act on", or by date when it's a schedule. Say which.

## 5. Options comparison

```
**Three options for the anniversary trip** *(general travel knowledge; verify pricing and availability)*

| | Small-ship Mediterranean | River: Douro | Expedition: Norway |
|---|---|---|---|
| **Fits because** | Loved small-ship cruising | Wine, slow pace | Wildlife, Arctic light |
| **Trade-off** | Busier ports in summer | Fewer wildlife moments | Weather-dependent |
| **To verify** | 🔍 fares, space, perks | 🔍 fares, space, perks | 🔍 fares, space, perks |

💡 **Top pick: Norway expedition.** It matches their wildlife interest and they haven't done an expedition voyage.
```

## 6. Report / summary

```
## October commission snapshot
*Confirmed bookings · by commission due date · CAD · 143 of 143 records*

**Headline:** CAD 45,200 expected, CAD 12,800 overdue ▲ 18% vs September

| Supplier | Bookings | Expected | Overdue |
|---|---:|---:|---:|
| Celebrity Cruises | 12 | CAD 18,500 | ❌ CAD 8,200 |
| Marriott Hotels | 28 | CAD 12,300 | ⚠️ CAD 2,000 |
| Others | 45 | CAD 14,400 | 0 |

**What to do first**
1. Follow up Celebrity Cruises (45 days average overdue).
2. Review the 2 bookings with no commission due date.

Want this by advisor, or as a spreadsheet?
```

For anything beyond ~25 lines, give this summary and offer a document or spreadsheet.

## 7. Confirmation prompt (before an action)

State what will happen, what cascades, and ask one clear question.

```
**Ready to cancel the Doe Lisbon trip** (May 3–10, 2027)

This will also cancel:
- 1 active booking: Four Seasons Lisbon (conf. ABC123)
- 1 active client payment: Planning fee, CAD 250.00

> ⚠️ Cancelling does not refund anything automatically. Do you want me to record refunds as part of this?

Reply **yes** to cancel, or tell me what to change.
```

## 8. Action completed

```
✅ **Created trip "Lisbon – Doe (May 2027)"** for Jane Doe, May 3–10, 2027, advisor Sam Spencer. [Open in TripSuite](link)

Next: add the hotel booking, or set a deposit reminder?
```

State the outcome in the first line, then only what changed. Report amounts the system returned, not your own arithmetic.

## 9. Error / blocked

Lead with what happened, why in plain words, and what you need or will do.

```
> ❌ **Couldn't save the booking.** The supplier payments add up to USD 2,100.00 but the booking total is USD 2,400.00.

To fix it I need one of:
1. The missing USD 300.00 payment (method and due date), or
2. A corrected booking total.
```

Never paste raw stack traces, JSON errors, or IDs; paraphrase with names. Include the exact error text only if the user asks.

## 10. No results / partial results

```
ℹ️ I found no clients matching "Xyzabc" (searched names and emails, active clients only).

Want me to try a looser spelling, include inactive clients, or create a new client?
```

```
> ⚠️ **Partial results:** I read 500 of 2,674 trips, so these totals only cover trips created since March. Say the word and I'll read the rest.
```

## 11. Disambiguation (several matches)

```
I found 3 clients named Smith. Which one?

1. **John Smith**: john.smith@email.com · advisor Sam · 4 trips
2. **Sarah Smith**: sarah.smith@email.com · advisor David · 1 trip
3. **Robert Smith**: robert.smith@email.com · advisor Sam · 7 trips
```

Number the options so the user can reply "2". Show enough to tell them apart.

## 12. Steps / how-to

```
**To add a deposit to the Four Seasons booking**
1. Tell me the amount, due date, and payment method.
2. I'll check the methods your agency allows.
3. I'll add it as pending, and mark it paid once you confirm it was sent.
```

## 13. JSON and code

Pretty-print and tag the language. Don't paste raw one-line JSON.

````
```json
{
  "trip": "Lisbon – Doe",
  "dates": ["2027-05-03", "2027-05-10"],
  "status": "active"
}
```
````

Summarize first; show the JSON only if it will be copied or the user asked.

## 14. Anti-patterns

| Don't | Do instead |
|---|---|
| ANSI color codes (`\x1b[31m`) in chat | ❌ icon + **bold** + a blockquote callout |
| Color as the only signal ("shown in red") | Icon **and** word ("❌ Overdue") |
| Table for 1–2 facts | A sentence |
| 8+ column tables | Split, drop, or switch to a list per record |
| Emoji in every line or heading | One icon per row, only when it signals status |
| Headers on a 3-line reply | Plain prose |
| Dumping 100 rows | Top 10 + "showing 10 of 143" + offer |
| Raw IDs, etags, stack traces | Names, labels, plain-language cause |
| Process narration ("First I searched…") | The result, then scope |
| Nested bullets 3+ levels deep | Flatten, or use a table |
| Bold everywhere | Bold only the headline, labels, and the one thing that matters |

### Agency-specific additions (Oceans & Rivers Travel)
- Keep **source labels** short and in the scope line or a lead-in: *From TripSuite*, *From virtuoso.com (checked Oct 5)*, *General travel knowledge*. Use 🔍 for **[Verify]** items.
- **Client-facing text** (proposals, emails): no emoji, no internal flags, no commission details; warm, polished prose.
- **Sensitive data** (health, passport): mark 🔒 only when you must show it to the requesting staff member, and show only what's needed.
