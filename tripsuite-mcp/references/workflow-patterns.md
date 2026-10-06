# Workflow patterns: inquiry, analytics, and reporting

Design patterns for multi-step **read and analysis** tasks, adapted from a generic "MCP Travel System" playbook onto the tools TripSuite actually exposes. (Write recipes live in `workflows.md`; this file is about answering questions well.)

> **Important:** TripSuite has **no analytics endpoints**. There is no revenue-metrics, year-over-year, forecast, client-lifetime-value, travel-habits, vendor-performance, or "commission summary" tool. Those answers are *assembled by you* from searches. That means: define the metric with the user, say what you counted, say what you couldn't, and never present a number you didn't derive from returned data.

## Contents
1. [Design principles](#1-design-principles)
2. [Pattern types](#2-pattern-types)
3. [Generic-tool → TripSuite mapping](#3-generic-tool--tripsuite-mapping)
4. [Client inquiry workflows](#4-client-inquiry-workflows)
5. [Financial analysis workflows](#5-financial-analysis-workflows)
6. [Commission tracking workflows](#6-commission-tracking-workflows)
7. [Trip and pipeline workflows](#7-trip-and-pipeline-workflows)
8. [Supplier analysis workflows](#8-supplier-analysis-workflows)
9. [Monthly business report](#9-monthly-business-report)
10. [Multi-step query patterns](#10-multi-step-query-patterns)
11. [Handling ambiguous requests](#11-handling-ambiguous-requests)
12. [Response formatting](#12-response-formatting)
13. [Error recovery](#13-error-recovery)

---

## 1. Design principles

1. **Most specific tool first.** Exact `id` beats `q`; `trip_search` for trips, `booking_search` only for supplier reservations; `commission_search` for commission receipts.
2. **Progressive detail.** Start with a narrow, trimmed list (`fields=`, `count`), then drill into one record with `id` + `expand`. Don't `expand` everything on a list.
3. **Minimize calls, maximize parallelism.** Independent lookups (a trip's bookings, payments, invoices, tasks) go in the **same turn**. Sequence only when one result supplies an ID for the next.
4. **Filter server-side.** Use date windows, `status_in`, `stage_in`, `clientId`, `tripId`, `supplierId`. Don't page through everything and filter in your head.
5. **Be explicit about scope.** Every analytic answer states: the date window, which records were included (e.g. "confirmed bookings, by check-in date"), the currency, and whether you saw all `total_count` rows or only the first N.
6. **Defaults for reads, questions for writes.** For a vague *read* ("what's our revenue?"), state the assumption you used and offer to change it. For *writes*, ask (see `SKILL.md`).
7. **No invented metrics.** If TripSuite doesn't store it (LTV, "VIP score", forecast, vendor rating), either derive it transparently from data or say it isn't available.

## 2. Pattern types

| Pattern | Use when | TripSuite example |
|---|---|---|
| **Single query** | One tool answers it | "What's Jane's email?" → `client_search q="Jane Doe"` |
| **Sequential** | Each step needs an ID from the last | client → trips → bookings → expenses |
| **Parallel** | Independent facts about one anchor | trip → bookings ∥ client payments ∥ invoices ∥ tasks |
| **Conditional** | Next step depends on the result | 1 client match → continue; many → ask; none → loosen search or offer to create |
| **Aggregation** | Combine many results into a number | Sum `totalHome` over bookings in a window; tally destinations per client |

## 3. Generic-tool → TripSuite mapping

The source playbook used these names. They do **not** exist here; use the right-hand column.

| Generic name | TripSuite equivalent | Gap / caveat |
|---|---|---|
| `search_clients` | `client_search` (`q`, `email`, `phone_like`, `*_like`, `expand=tags,tripCount`) | `client_status`/"VIP" → only `tag` (e.g. `tag="VIP"`) if the org uses such a tag |
| `get_client_profile` | `client_search id=` + `client_profile_view sections=[…]` | Identify by **UUID**, not email. No lifetime-value field |
| `get_client_bookings` | `booking_search clientId=` (+ date window) and/or `trip_search clientId=` | `booking_search clientId` matches the booking's **primary client** only; trip-level history via `trip_search` is more complete |
| `get_client_preferences` | `client_profile_view sections=[preferences,health]` | Preferences are airline/seat/class, hotels, bed size, notes |
| `get_client_loyalty_programs` | `client_profile_view sections=[programs]` | |
| `get_client_travel_habits` / `analyze_client_destinations` | **Not available.** Derive: `trip_search clientId= fields=destinations,startDate,endDate` and tally | You compute frequency/avg duration; label it as derived |
| `search_clients_by_preferences` | **Not available** | No preference search. Could proxy with `trip_search q="<destination>"` or tags; per-client profile scans are slow and sensitive. Say so |
| `get_revenue_metrics`, `get_revenue_by_category`, `get_yoy_comparison`, `get_financial_summary` | **Not available.** Derive from `booking_search` (+`expand=supplier`), `client_payment_search`, `commission_search`, statements | See §5 |
| `get_revenue_forecast`, `get_commission_pipeline` | **Not available.** Report booked/pending data only | No prediction tool. Don't fabricate forecasts |
| `get_trip_pipeline`, `search_itineraries` | `trip_stage_list` + `trip_search stage_in=` / date windows | Trips have no price; sum their bookings if value is wanted |
| `get_upcoming_departures` | `trip_search startDate_gte=<today> startDate_lt=<today+N> status_in=active` | |
| `get_itinerary` | `trip_search id=` + `booking_search tripId= expand=components` | |
| `get_commission_summary`, `get_overdue_commissions`, `get_commissions_by_advisor` | `booking_search` commission `fields` + `commission_search`; advisor payouts via statements | See §6 |
| `get_vendor_info`, `search_vendors` | `supplier_search` | No performance/"preferred" flag; look at `tags`, `isRetired`, `parentId` |
| `get_top_destinations` | **Not available.** Derive: `trip_search` window, tally `destinations` | Cap the sample and say so |
| Other systems named in the source (Travefy, OceanRiver) | **Not exposed** by this MCP | Don't mention data from them |

Identifiers: the source used **emails** as keys. TripSuite uses **UUIDs**: use one directly if you have it; if you only have a name/email, search, **confirm the match with the user**, then use `data[].id` (see `id-resolution.md` §0).

## 4. Client inquiry workflows

### A. "Tell me about client John Smith"
```
client_search q="John Smith" expand=tags,tripCount
 ├─ 1 match → CONFIRM with user first, then in parallel:
 │     client_profile_view id= sections=[personal,preferences,programs]   (only what's needed)
 │     trip_search clientId= sort=-startDate expand=configuredStage limit=5
 │     client_payment_search clientId= status_in=active (open balances, if relevant)
 ├─ >1 match → list candidates (name, email, advisor, trip count) and ask
 └─ 0 → loosen (lastName_like), then offer to create
```
Report: name, contact, advisor, tags, trip count, last trip, upcoming trip(s), open payments. **Don't** report lifetime value unless you derived it and show how.

### B. "What has Sarah booked in the past year?"
1. `client_search` → id.
2. In parallel: `trip_search clientId= startDate_gte=<12 mo ago> sort=-startDate expand=primaryClient` and `booking_search clientId= startDate_gte=<12 mo ago> expand=supplier fields=confirmationNumber,status,startDate,endDate,totalAmount,supplierId`.
3. Group by trip; show supplier, dates, total + currency, status.
4. Tally destinations only if asked ("derived from trip destinations").

### C. "What does the Miller family prefer?"
1. `client_search q="Miller"` → pick members; or `group_search q="Miller" expand=members` if they're a leisure group (`group_member_list`).
2. For each member (cap at ~5), `client_profile_view sections=[preferences,health,programs]`.
3. Destination history: `trip_search clientId= fields=destinations,startDate` → tally.
4. Present per person; mark which items are stored preferences vs derived. Health data only if relevant to the question; don't recite it unprompted.

## 5. Financial analysis workflows

**First, pin down what "revenue" means** and say which you used. In TripSuite terms:

| Meaning | Source | Notes |
|---|---|---|
| **Sales volume (booked)** | Sum `totalHome` (or `totalAmount` in one currency) of bookings in a window | Choose and state the date axis: `createdAt` (booked), `startDate` (travel), or `bookedDate`. Exclude `status` canceled/voided unless asked |
| **Agency commission** | Booking `estimatedCommission` (expected) and `commission_search` (received) | Expected ≠ received |
| **Fees billed/collected** | `client_payment_search invoiceFor=FEES status_in=paid` | |
| **Advisor payouts** | `statement_*` | Period-based, not prorated; payouts, not revenue |
| **Collected from clients** | `client_payment_search status_in=paid` (and `paidAt`) | |

### "What's our revenue this quarter?"
1. `organization_view` → `homeCurrency` (use `totalHome` fields so figures are comparable).
2. `booking_search` with the window on the agreed date axis, `status_in=confirmed`, `fields=id,totalHome,totalAmount,currency,startDate,supplierId,estimatedCommission`, `expand=supplier` (for type), `count=true`; page through (cursor, `limit=500`).
3. Aggregate yourself: total, by month, by supplier type (`supplier.type`: HOTEL, CRUISE_LINE, AIRLINE…).
4. Optionally add fees (`client_payment_search invoiceFor=FEES`) and commission received (`commission_search`).
5. **Year over year:** repeat step 2–3 for the same window one year earlier and compute the deltas. Show both windows.
6. State: window, axis, statuses included, currency, number of bookings, and any truncation.

> Don't copy a "revenue = $1,245,000" style template with numbers you didn't compute.

### "Give me a financial summary" (MTD default)
State the assumption ("month to date, by booking created date"), then in parallel: booked volume, commission expected vs received (`commission_search receivedDate`), fees billed vs paid, open client payments due (`client_payment_search status_in=active dueDate_lt=…`), and trips departing soon. Offer drill-downs.

### "What revenue can we expect next quarter?"
There is no forecast tool. Report what's **already booked**: bookings with `startDate` in the window, expected commission by `commissionDueDate`, client payments due. If the user wants a projection, say it's a simple extrapolation from history you computed, show the method, and label it an estimate.

## 6. Commission tracking workflows

Commission data lives in two places: **booking fields** (expected: `estimatedCommission`, `commissionDueDate`, `commissionStatus`, `supplierCommissionState`, `commissionPaidAt`) and **`commission_search`** (received records: `amountHome`, `receivedDate`, `reconciledAt`, `supplierNameActual`).

> The allowed values of `commissionStatus` / `supplierCommissionState` aren't documented in the tool schemas. Fetch a few real bookings first and read the values before you filter or define "pending/overdue".

### "Show me pending commissions"
1. `booking_search status_in=confirmed fields=id,confirmationNumber,estimatedCommission,commissionDueDate,commissionStatus,supplierCommissionState,commissionPaidAt,currency,supplierId expand=supplier` (window as needed; page).
2. Keep rows where commission is expected and not yet paid (per the status values you observed; `commissionPaidAt` empty).
3. Group by supplier (and count bookings). Sum `estimatedCommission` (note currencies).
4. **Overdue** = pending with `commissionDueDate` < today. Bucket by days overdue (e.g. 1–30, 31–60, 60+).
5. Cross-check received with `commission_search` for the same bookings/window if the user asks "what did we actually get".

Report: total pending, by supplier, overdue buckets, and the **action items** (largest overdue suppliers). Offer the commission invoice PDF (`booking_supplier_invoice_download`, confirmed bookings only).

### "How are our agents doing on commissions?"
- Expected commission by advisor: `booking_search expand=advisor,splits` over the window and group by advisor (honor `splits` takePercent if you present per-advisor shares; say if you ignored splits).
- Actual payouts: statements (`statement_summary_list` → `statement_recipient_search` → `statement_user_view`), if the caller's role can see them.

### "Which suppliers owe us the most?"
Same as pending, grouped by supplier, sorted descending, plus overdue column.

## 7. Trip and pipeline workflows

### Upcoming departures
`trip_search startDate_gte=<today> startDate_lt=<today+N days> status_in=active sort=startDate expand=primaryClient,advisor` → table: trip, client, advisor, departure date. Drill: `trip_search id=` + `booking_search tripId= expand=components`. Flag trips with no bookings, unconfirmed bookings (`isConfirmed:false`/`pending`), or unpaid client payments due.

### Pipeline analysis
1. `trip_stage_list` → stages (org-specific, e.g. Lead / Planning / Booked / Declined / Lost).
2. For each relevant stage: `trip_search stage_in=<id> status_in=active count=true limit=1` to get counts cheaply; fetch rows only for stages the user cares about.
3. Value (optional): sum `totalHome` of those trips' bookings (`booking_search tripId=` per trip, or by window). It's expensive: do it for a bounded set and say so.
4. "Quoted" or other pipeline wording → match to the org's actual stage names; ask if unclear.

## 8. Supplier analysis workflows

- **Find suppliers:** `supplier_search type_in=HOTEL q=… isRetired=false`. There's no "preferred" flag; check `tags` (`expand=tags`) and badges only if the user says how the org marks preferred ones.
- **"How is Celebrity Cruises performing?"** → `supplier_search name="Celebrity Cruises"` → in parallel: `booking_search supplierId= status_in=confirmed` (window) for volume/value, `commission_search` and booking commission fields for commission expected vs received. Summarize volume, value, commission, overdue. Be clear there is **no performance score**; you're reporting activity.
- **Compare suppliers:** repeat per supplier and tabulate the same metrics; recommendations must be framed as observations from the data.

## 9. Monthly business report

Run in parallel (state the month and basis up front):
1. Booked volume by supplier type (§5) for the month.
2. Commission expected vs received (§6) and overdue.
3. Fees billed/collected (`client_payment_search invoiceFor=FEES`).
4. New clients (`client_search createdAt_gte/_lt count=true`), new trips (`trip_search createdAt_*`).
5. Departures in the next 30–60 days (§7) and open tasks (`task_search isCompleted=false dueAt_lt=…`).
6. Top destinations: sample trips for the month and tally `destinations` (state the sample size).

Present as a short report with a headline, 4–6 numbers, 2–3 flags needing action, and an offer to drill in. Use `count=false` on pages after the first.

## 10. Multi-step query patterns

**Identify → Detail → Analyze** ("Tell me about our cruise bookings this year")
`booking_search expand=supplier` window + client-side filter `supplier.type=CRUISE_LINE` (or `supplier_search type_in=CRUISE_LINE` → `supplierId` filter) → `booking_search id=` for the largest few → aggregate totals/commission.

**Search → Verify → Act** ("Find the Thompson Maldives booking")
`client_search q=Thompson` → `trip_search clientId= q="Maldives"` (destinations are searchable) → `booking_search tripId=` → exact fetch for details. Confirm the right trip with the user before any write.

**Aggregate → Compare → Recommend** ("Which suppliers should we focus on?")
Volume and commission by supplier over a stated window → compare expected vs received and overdue → present observations and a suggested focus, clearly marked as your interpretation.

## 11. Handling ambiguous requests

| Ambiguity | Read request: do this | Write request: do this |
|---|---|---|
| **Missing time period** ("What's our revenue?") | Use month-to-date, say so, offer quarter/custom | Ask |
| **Unclear client** ("Smith's bookings") | UUID known → use it. Otherwise `client_search`, then confirm: one match → "Is this the right Smith?"; several → list (name, email, advisor, trips) and ask | Same; never guess |
| **Vague metric** ("How are we doing?") | Short MTD summary (§5) + offer drill-downs: revenue, commission, client activity, pipeline | n/a |
| **Comparison without baseline** ("Is our revenue good?") | Compute the same window last year and show the delta; say "good" is relative | n/a |
| **Two plausible record types** (trip vs booking; fee vs trip-cost payment) | Pick the likelier and say which; offer the other | Ask; see `money-flows.md` |
| **"Paid"/"overdue" undefined** | State your definition (e.g. due date passed and status active) | Ask |

## 12. Response formatting

- **Lead with the answer**, then scope, then flags, then an offer for more.
- **Client inquiries:** name, contact, advisor/status/tags, recent and upcoming trips, open balances. Offer detail.
- **Financial:** totals first, then breakdowns; percentages and ↑↓→ trend markers for comparisons; always state window, basis, currency, and record count. If not all rows were read, say "first N of M".
- **Commission tracking:** highlight overdue and action items; group by supplier/advisor; show expected vs received; flag exceptions (missing due dates, unconfirmed bookings).
- **Trip planning:** match to stored preferences/loyalty programs; mention booking windows and open items.
- **Names, not IDs**: convert every UUID/ID field to a name or descriptive label before reporting (full table in `SKILL.md` → "Showing records to the user"). Request `expand=` (e.g. `primaryClient,advisor,supplier,configuredStage`) on the first call so names arrive with the data, and resolve each distinct ID once. Link with `appUrl`. Show currency codes; don't mix currencies in a sum without saying so.

Template skeleton (fill only with values you retrieved):
```
<Headline answer>
Scope: <window> · <basis> · <currency> · <N records of M>
• <breakdown line> …
Flags: <overdue / missing / unusual>
Want me to drill into <A>, <B>, or <C>?
```

## 13. Error recovery

- **No results:** say what you searched, then offer: different criteria, looser name match (`lastName_like`), include inactive (`isActive` omitted / `includeInactive`), or create. Remember results are permission-scoped.
- **Multiple interpretations:** list 2–3 and ask which.
- **Partial results:** if some calls failed or you truncated pagination, say exactly what's missing ("read 500 of 2,674 trips") and what you'd do to complete it.
- **Feature not available:** name the missing capability (e.g. "TripSuite doesn't provide forecasts"), give the closest derivable answer, and, if it blocks the task, `feedback_submit` with `missing_capability`.
- **Tool/validation errors:** see `gotchas-and-errors.md`; fix the specific problem; don't loop.
