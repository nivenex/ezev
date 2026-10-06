# Working with the TripSuite skill (`tripsuite-mcp`)

This skill (the agency's voice, sourcing rules, planning and analysis) sits **on top of** the **`tripsuite-mcp`** skill (how to operate the TripSuite MCP server correctly). Every time you touch the agency's records you use both: this one decides *what you may say and how*, `tripsuite-mcp` decides *how data is read and changed*.

## Contents
1. [Hand-off protocol (mandatory)](#1-hand-off-protocol-mandatory)
2. [Who governs what, and precedence](#2-who-governs-what-and-precedence)
3. [Operating rules that always apply](#3-operating-rules-that-always-apply)
4. [Task map: travel-agent job → TripSuite calls → what to read](#4-task-map)
5. [Presenting TripSuite results in the agency's voice](#5-presenting-tripsuite-results)
6. [Suppliers: three sources, never merged](#6-suppliers-three-sources-never-merged)
7. [Combined flows](#7-combined-flows)
8. [When something is missing or fails](#8-when-something-is-missing-or-fails)
9. [Keeping the two skills in sync](#9-keeping-the-two-skills-in-sync)

---

## 1. Hand-off protocol (mandatory)

Before the **first** TripSuite call in a conversation:

1. **Read the `tripsuite-mcp` skill's `SKILL.md`.** Invoke it by name if you have a skill tool; otherwise read its file (in this environment: `/mnt/skills/plugins/tripsuite-mcp/SKILL.md`, or find it in the available-skills list). Do this **once per conversation**, even for a read-only question.
2. **Then read the reference for the job** (see §4). Always read `references/money-flows.md` **before any write that involves an amount**, and `references/workflows.md` before a create/cancel/booking recipe. Use `references/workflow-patterns.md` for analysis and reporting.
3. **Load the tools.** TripSuite tools are named `mcp__TripSuite__<name>` and may be **deferred**: run a tool search for the names you need and use the returned schemas. **Don't guess parameter names.**
4. **Orient once:** `user_current_view` (access level, current advisor, organization id). If money is involved, `organization_view` for home currency and accepted client-payment currencies.
5. **Execute under the rules in §3, then answer in the agency's voice (§5).**

Skipping step 1 or 2 because "it's just a lookup" is the main way the integration breaks: the skill carries the lookup pitfalls (ID chains, `expand`, pagination, replace-vs-merge) that make results accurate.

## 2. Who governs what, and precedence

| Topic | Governed by |
|---|---|
| Which tool to call, parameters, ID lookups, `ifMatch`/etag, pagination, money model (client payment vs trip invoice vs supplier payment vs commission), cancel/void/delete semantics, error handling | **`tripsuite-mcp`** |
| What you may say beyond the data, source tiers and labels, the "no invention" rule, Virtuoso lookups, tone and voice, trip-planning method, business-analysis frameworks, agency facts | **This skill** |
| Confirmation before cancel/void/delete and before using a search-matched record; names instead of IDs; no invented financial values | **Both. The stricter wording wins** (see §3) |

**Conflicts:** data integrity, privacy, and safety → follow `tripsuite-mcp` (or the stricter rule). Voice, labelling, and what counts as an acceptable source → follow this skill. Enthusiasm and sales instinct never override a confirmation. A user's explicit approval of the **specific identified action** is the confirmation; a general "just do it" before you've shown which record is not.

## 3. Operating rules that always apply

These are restated here **on purpose**: older copies of `tripsuite-mcp` don't contain the first two, and this skill must behave correctly either way. If `tripsuite-mcp` says the same, great; if it says something stricter, follow that.

1. **UUID first; search only when you only have a name/email; then confirm.** If you hold a UUID (pasted, from an `appUrl`, earlier result, or already confirmed), use it directly. If you only have a name, email, phone, or description, search, then **show the match (name, email/contact, advisor, one distinguishing detail) and get the user's yes before using it**; one match is still confirmed; several are listed; none is reported. Batch confirmations with the plan ("Create the fee for Jane Doe on the Lisbon trip. OK?"). After a yes, remember the UUID and don't re-ask. A UUID that fails to resolve is **reported, never silently replaced by a name search.**
2. **Names, never raw IDs, in everything you say.** Ask for names up front with `expand=` (e.g. `primaryClient`, `advisor`, `supplier`, `configuredStage`, `trip`, `client`) and resolve each distinct ID once. If a name can't be resolved say so, don't print the UUID. Public IDs (e.g. `J37CFX8HJ`), confirmation numbers, and `appUrl` links are fine. Never show etags. UUIDs are for tool calls only unless the user asks for one.
3. **Fresh fetch → `ifMatch` → write.** Updates, cancels, and most financial changes need the `etag` from an exact-id fetch done just now. On a conflict, re-fetch and reconsider; don't force.
4. **Confirm before cancel / void / delete**, and before money-affecting writes when anything was inferred. Describe what cascades (e.g. cancelling a trip cancels its active bookings and client payments).
5. **Never invent or compute financial values.** Don't assume `payingEntity` or commissionability, don't invent confirmation numbers, don't compute `totalCharged` or exchange rates. Ask, or use what the system returns.
6. **Replace-vs-merge:** tags, destination lists, invoice line items, profile `health`/`dates`/`preferences` blocks, and similar fields replace the whole value. Read, then send the complete desired set.
7. **Minimum necessary data.** Request only the profile sections the task needs; don't repeat health/passport details unprompted; keep them out of client-facing text.
8. **Report only what came back.** "None recorded" is not "none". If a list was truncated, say how many you read of the total.

## 4. Task map

"Read" means the `tripsuite-mcp` file to open after its `SKILL.md`. Section numbers are in that skill's files.

| Job | TripSuite calls (typical) | Read |
|---|---|---|
| **Client lookup / "tell me about X"** | `client_search` → `client_profile_view` (needed sections only) ∥ `trip_search clientId=` ∥ `client_payment_search clientId=` | `workflow-patterns.md` §4A, `workflows.md` §1 |
| **What a client has booked / likes** | `trip_search clientId= fields=destinations,…` ∥ `booking_search clientId= expand=supplier` ∥ `client_profile_view sections=[preferences,programs]` | `workflow-patterns.md` §4B–C |
| **Planning grounding** (before suggesting a trip) | same as above; add `group_search clientId=` for traveling companions | this skill's `trip-planning-playbook.md` §2 |
| **Upcoming departures** | `trip_search startDate_gte= startDate_lt= status_in=active expand=primaryClient,advisor` | `workflow-patterns.md` §7 |
| **Everything about one trip** | `trip_search id=` ∥ `booking_search tripId=` ∥ `client_payment_search tripId=` ∥ `trip_invoice_search tripId=` ∥ `task_search tripId=` | `workflows.md` §4 |
| **Our history with a supplier** | `supplier_search name=` → `booking_search supplierId=` (+ commission fields) ∥ `commission_search` | `workflow-patterns.md` §8 |
| **New client / new trip** | `client_search` (dup check) → `destination_search` → `trip_search` (overlap check) → `client_save` / `trip_save` | `workflows.md` §2–3 |
| **Book a supplier confirmation** | `booking_source_extract` → `supplier_search` → `booking_save create_booking` → verify | `workflows.md` §5, **`money-flows.md` first** |
| **Supplier payments / client fees / invoices / refunds** | `booking_payment_to_supplier_method_list`, `booking_financial_save`, `client_payment_save`, `trip_invoice_save`, `client_payment_refund`, `booking_refund_create` | **`money-flows.md`**, `workflows.md` §7–11, §13 |
| **Cancel a booking or trip** | exact fetch → list what cascades → confirm → `booking_cancel` / `trip_cancel` | `workflows.md` §12, confirmation matrix in `SKILL.md` |
| **Follow-ups and reminders** | `task_search` / `task_save` (must link a trip or client) | `workflows.md` §16 |
| **Group voyage status** | `group_search` / `trip_search tag=` → bookings and payments per traveler | `workflows.md` §17, `workflow-patterns.md` §4 |
| **Update dietary/health/preferences/addresses** | `client_profile_view` → `client_profile_save` (complete blocks) | `workflows.md` §15, `gotchas-and-errors.md` §1 |
| **Revenue, commission, pipeline, monthly report, SWOT data** | derived from `booking_search`, `client_payment_search`, `commission_search`, `trip_search`, statements | `workflow-patterns.md` §5–9; this skill's `business-analysis.md` |
| **Advisor payouts** | `statement_summary_list` → `statement_recipient_search` → `statement_user_view` | `workflows.md` §18 |
| **Attach a supplier quote/confirmation** | `attachment_create` (≤256 KB inline) or upload-URL flow | `workflows.md` §19 |

TripSuite has **no analytics, forecast, or lifetime-value endpoints**. Every figure in a report is derived by you from searches, so state window, basis, currency, and record counts (see `business-analysis.md`).

## 5. Presenting TripSuite results

- **Label the source:** "From TripSuite: …". Use "Not found in TripSuite" or "none recorded in TripSuite" when empty. Never fill gaps with plausible detail.
- **Names and links:** primary column is a name or descriptive label (supplier + confirmation number + dates for a booking; subject + amount + due date for a payment). Add the `appUrl` link for records you created or point to.
- **Scope line for any aggregate:** window · date basis · currency · statuses included · "N of M records read".
- **Raw tool output is not the answer.** Some endpoints return extra fields or only IDs (for example, task rows carry trip and advisor IDs, not names); fetch names with `expand=` and show only what the question needs.
- **Flags that matter to advisors:** unconfirmed bookings, missing confirmation numbers, overdue or soon-due payments, commissions overdue, open tasks. Lead with them.
- **Voice:** warm, expert, and concise. After the data, add one useful next step ("Want me to draft the follow-up task?").
- **Volatile facts still need a source** even if TripSuite is the only data you used (e.g. a stored price is "per the booking record", not a current fare).

## 6. Suppliers: three sources, never merged

| Question | Source | Tool/file |
|---|---|---|
| "What have **we** booked with X? Commission history? Defaults?" | **TripSuite** | `supplier_search`, `booking_search supplierId=`, `commission_search` |
| "Is X a **Virtuoso preferred partner**? What perks does Virtuoso list?" | **virtuoso.com** | `virtuoso-partner-lookup.md` |
| "Has our **team** sailed with X?" | **Agency profile** | `agency-profile.md` |

A supplier appearing in TripSuite does **not** make it a preferred partner; a team member's voyage with it does not either. If the agency marks preferred suppliers with a TripSuite tag, treat it as a hint, confirm the convention with the user, and still verify on Virtuoso. Updating supplier tags is a write: read existing tags first (tag lists replace) and confirm.

## 7. Combined flows

**A. Proposal for a returning client, then booking**
1. Confirm the client (UUID, or search then confirm) → pull profile preferences, trip and booking history (§4).
2. Draft options using this skill's playbook (general expertise, labelled; **[Verify]** volatile facts).
3. Verify any supplier's Virtuoso status on virtuoso.com; report with link and date.
4. Draft the proposal from `assets/proposal-template.md`, filling prices/inclusions only from the supplier quote.
5. After a yes: `tripsuite-mcp` flow: trip (dup check) → `booking_source_extract` → ask who pays the supplier, commissionable?, payment schedule → summarize → `booking_save` → verify → offer tasks.

**B. "Which commissions are overdue and who owes us?"**
`workflow-patterns.md` §6 (inspect real status values first) → group by supplier → state scope line → offer `booking_supplier_invoice_download` for confirmed bookings → offer follow-up tasks (`task_save`, with confirmation).

**C. "How's the Antarctica group looking?"**
Identify the trip/group (UUID or search + confirm) → travelers' bookings, client payments, open tasks → summarize confirmed / owing / outstanding by traveler → flag gaps. No group pricing or perks stated without a source.

## 8. When something is missing or fails

| Situation | What to do |
|---|---|
| **`tripsuite-mcp` skill not available** | Read and write behavior still follows §3. Reads are fine. For **money writes, booking creation, cancel/void/delete**, tell the user the TripSuite skill isn't loaded and recommend installing it first; proceed only if they explicitly accept the risk, after you've read each tool's schema carefully. Low-risk writes (tasks, tags) are fine with confirmation. |
| **TripSuite tools not connected / not loadable** | Say so plainly. Don't invent records. Offer what you can do without it (agency profile, Virtuoso lookup, general planning ideas, analysis frameworks with user-supplied numbers). |
| **Not found / not visible** | "Not found in TripSuite (or not visible to your account)." Results are permission-scoped; suggest checking with an admin if a duplicate-email error contradicts an empty search. |
| **Validation or conflict error** | Read the error, fix the specific cause, explain in plain language with names. Don't retry blindly or "work around" guardrails. See `tripsuite-mcp` → `gotchas-and-errors.md`. |
| **Capability gap blocks the task** | Say it isn't exposed; give the closest supported path; `feedback_submit` (no customer data) if it's blocking. |
| **Older `tripsuite-mcp` copy** | Rely on §3 here for UUID-first/confirm and names-not-IDs; tell the user a newer `tripsuite-mcp` is available if you notice behaviors missing. |

## 9. Keeping the two skills in sync

`scripts/check_tripsuite_refs.py <path-to-tripsuite-mcp-skill>` verifies that every TripSuite tool name and file path mentioned in this skill exists in the given `tripsuite-mcp` copy, and reports whether that copy contains the UUID-first and names-not-IDs sections. Re-run it whenever either skill changes.
