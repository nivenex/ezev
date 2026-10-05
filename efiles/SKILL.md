---
name: tripsuite-mcp
description: How to correctly use the TripSuite MCP server (tools named mcp__TripSuite__*), a travel-agency CRM/back-office for clients, trips, bookings, itinerary components, suppliers, client payments, trip invoices, supplier payments, commissions, tasks, groups, corporate accounts, and advisor statements. Use whenever the user asks to look up, create, change, cancel, bill, or report on anything a travel advisor tracks (client, traveler, trip, itinerary, reservation, hotel, flight, cruise, supplier, deposit, invoice, fee, refund, commission, task, payout), even without saying "TripSuite", and whenever TripSuite tools are available. Covers ID lookup chains, etag/ifMatch concurrency, the four kinds of money (client payment vs trip invoice vs supplier payment vs commission), confirmation rules for deletes/cancels/voids, replace-vs-merge writes, and workflows. Read BEFORE the first TripSuite write.
---

# TripSuite MCP

TripSuite is a back-office system for travel agencies. The MCP server exposes ~65 tools that read and write clients, trips, bookings, money, and tasks. The tools are well documented individually, but several concepts span many tools and are easy to get wrong in ways that corrupt financial records. This skill gives you the mental model, the rules that prevent those mistakes, and pointers to deeper references.

> Tool names appear as `mcp__TripSuite__<name>` in most clients. This skill uses the bare `<name>` (e.g. `trip_search`). In some clients tools are deferred: if a tool's schema isn't loaded, run a tool search for its name first. Don't guess parameter names.

## Where to look next

| Need | Read |
|---|---|
| Which tool does X? Args, returns, caveats for every tool | `references/tool-catalog.md` |
| "Where do I get this UUID?" / which writes need `ifMatch` | `references/id-resolution.md` |
| Anything involving money: payments, invoices, refunds, commissions, paying entity | `references/money-flows.md` (**read before any money write**) |
| Step-by-step recipes (create trip, book from supplier doc, cancel, bill, report…) | `references/workflows.md` |
| Building/editing itinerary components (air, hotel, cruise, …) and date/time formats | `references/booking-components.md` |
| Errors, locked/ARC records, duplicates, "why did this fail" | `references/gotchas-and-errors.md` |
| Copy-and-adapt request payloads | `assets/examples/*.json` |
| Sanity-check a payload before sending; generate UUIDv4s | `scripts/lint_payload.py`, `scripts/new_uuid.py` |

## Mental model

```
Organization ── Agency ── Advisor (agency membership, "advisorId")      User (person, "userId")
                              │ owns
   Client ──(member of)── Group (leisure)   /   Corporate client (company)
     │ primary traveler
     ▼
   TRIP ── destinations, tags, pipeline stage ("Status"), advisor
     ├── BOOKING (one supplier reservation) ── COMPONENTS (air, hotel, cruise, tour, transfer, rail, car, dining, event, insurance)
     │       ├── payments to supplier ("expenses")   money OUT
     │       ├── refunds
     │       └── commissions                          money IN from supplier (read-only here)
     ├── CLIENT PAYMENTS                               money IN from client (fees or agency-paid trip costs)
     ├── TRIP INVOICES                                 client-facing documents that reference the above
     └── TASKS, attachments
```

Two facts that trip people up constantly:

1. **User ID ≠ advisor ID.** `user_current_view` returns both. Trips, bookings, clients, tasks, groups reference the *advisorId* (agency membership). `statement_user_view` wants the *user* ID. `user_search` returns `data[].agencies[].advisorId` and `.agencyId`.
2. **Trip-level vs booking-level.** "My Paris trips", "trips I booked", trips for a client → `trip_search`. Only individual supplier reservations (confirmation numbers, a specific hotel/flight) → `booking_search`. A trip with no bookings never appears in `booking_search`, so an empty result there does not mean the trip doesn't exist.

## Response shapes (verified)

- List/search: `{ data: [...], pagination: { next_cursor, has_more, total_count, total_count_is_exact } }`
- Exact fetch (pass `id`): `{ etag: 'W/"updatedAt:…"', data: {...} }`
- **The `etag` is the "version" the tool descriptions refer to.** Copy it verbatim into `ifMatch` on the next write to that record. It sits at the top level, outside `data`, and only appears on exact-id fetches (not on list rows).
- Records carry `appUrl` (a link into the TripSuite web app). Give the user that link when you create or find something; it's more useful than a UUID.

## Ten rules that prevent most mistakes

1. **Orient first, once.** Call `user_current_view` (access level, `currentUserId`, `currentAdvisor.advisorId`, `organizationId`). Call `organization_view` with that `organizationId` when you need `homeCurrency` / `clientPaymentCurrencies`. `accessLevel: "user"` means writes default to the current advisor; `"organization"` means you must ask who the advisor/assignee is, because TripSuite never picks one.
2. **Search before you create.** Clients (email is unique per org), trips (overlap/within 30 days of the same client), suppliers (exact `name`), and also search before *retrying* a create that timed out. Visibility is permission-scoped: "no match" can still collide with a record the user can't see (a duplicate-email error is the tell; tell the user to ask an admin).
3. **Resolve ambiguity with the user, never silently.** More than one plausible client/trip/stage/destination/supplier → show 2–4 candidates (name + distinguishing detail) and ask. Never write against a guessed match.
4. **Fresh fetch → `ifMatch` → write.** Updates, cancels, deletes, and most financial changes need the `etag` from an exact-id fetch done *just now*. On a version conflict, re-fetch, re-read what changed, reconsider the change, and only then retry. Don't mention etags/`ifMatch` to the user unless asked. (Which tools need it: `references/id-resolution.md`.)
5. **Know replace vs merge.** Many fields replace the whole list or block: tags, `destinationIds`, invoice `lineItems`/`paymentMethodIds`, booking `splits`/`additionalClientIds`/`udids`, supplier lists, and profile `dates`/`health`/`preferences` blocks (omitted fields inside a provided block are **cleared**). To change one element, read the current value and send the full desired set. Details: `references/gotchas-and-errors.md`.
6. **Four kinds of money, four tool families.** Client payment (money IN from client), Trip Invoice (a document), payment to supplier (money OUT, lives on the booking), commission (money IN from supplier, read-only). Using the wrong one double-books or mis-bills. Read `references/money-flows.md` before any money write.
7. **Never compute or invent financial values.** Use the `totalCharged` the API returns, never your own processing-fee math. Omit `exchangeRate` unless the user explicitly gave one (TripSuite applies its canonical daily rate). Never invent confirmation numbers, PNRs, placeholder components, due dates, or payment methods. Ask.
8. **Ask for what the system requires and the user didn't say.** Common ones: `payingEntity` (CLIENT/AGENCY) and `isCommissionable` on bookings (never infer commissionability from a supplier default), `travelType` (leisure/corporate) on trips, payment method + due date + already-paid? on supplier payments, fee type on fees.
9. **Confirm before destructive or irreversible actions** (matrix below). State what will happen and what cascades, then wait for an explicit yes.
10. **Be sparing with sensitive data.** `client_profile_view` returns health, passport, and contact data. Request only the sections you need, don't paste them back unless asked, and never put them in client-facing fields (invoice `memo`/`terms`) or in `feedback_submit`.

## Confirmation matrix

| Action | Tools | Do this |
|---|---|---|
| Read / search | `*_search`, `*_view`, `*_list` | Just do it. Prefer narrow filters + `fields`. |
| Create / update (low stakes) | `client_save`, `task_save`, tags, groups | If the user gave the details, do it; summarize what you changed. |
| Create / update with money | `booking_save`, `booking_financial_save`, `client_payment_save`, `trip_invoice_save`, `booking_refund_create`, `client_payment_refund` | Summarize the exact amounts/currency/dates/paying entity first when anything was inferred or ambiguous; otherwise proceed and report back. |
| Record money as received/paid | `client_payment_mark_paid`, add/update payment with `paidDate` | Confirm method and date. |
| **Cancel** (cascades) | `trip_cancel` (cancels bookings + client payments, may record refunds), `booking_cancel` (last active booking cancels the trip) | List what will be cancelled, ask about refunds, get a yes. Cancel ≠ void ≠ delete. |
| **Void** (clears financial record) | `booking_void_or_delete` `void`, `client_payment_void_or_delete` `void` | Explain it clears sale amounts/voids related payments; get a yes. Not available for ARC or TripSuite-processed payments. |
| **Delete** (hide) | `*_delete`, `*_member_delete`, `client_profile_item_delete`, `booking_component_delete`, `booking_payment_to_supplier_delete` | Tool descriptions say deletes are reversible hide-only and require the user's confirmation first. Name the record, get a yes, then call. Don't refuse or lecture about permanence. |

If the user asks you to "delete" something that is better modeled as cancel/void/inactive (e.g. a client with history → `client_status_set` isActive=false; a trip that was booked → `trip_cancel`), say so and let them choose.

## Intent → tools (quick router)

| User wants… | Start with |
|---|---|
| Find a client | `client_search` (`q`, `email`, `phone_like`, `firstName_like`/`lastName_like`, `expand=tags,tripCount`) |
| A client's passport/health/prefs/addresses/loyalty | `client_profile_view` with only needed `sections` |
| New client / change name, email, phone, advisor | `client_save` (`create_client` / `update_client`) |
| Everything about a trip | `trip_search id=… expand=primaryClient,advisor,tags,configuredStage`, then `booking_search tripId=…`, `client_payment_search tripId=…`, `trip_invoice_search tripId=…`, `task_search tripId=…` |
| Upcoming/past trips | `trip_search startDate_gte`/`startDate_lt`, `status_in`, `sort=startDate` |
| New trip | `destination_search` → `trip_search` (dup check) → `trip_save create_trip` |
| Change pipeline "Status" | `trip_stage_list` → `trip_save set_stage` (allowed even on locked trips) |
| Book a hotel/flight/cruise from a supplier doc | `booking_source_extract` → `booking_save create_booking` (see workflow) |
| Edit itinerary pieces | `booking_search id=… expand=components` → `booking_component_view` → `booking_component_save` |
| Supplier deposit / final payment | `booking_payment_to_supplier_method_list` → `booking_financial_save add_payment_to_supplier` |
| Bill the client a fee | `client_payment_configuration_view fee_types` → `client_payment_save create` (FEES) |
| Bill the client for agency-paid travel | `client_payment_save create` (TRIP) → `trip_invoice_save` with REQUEST_PAYMENT |
| Have client approve a client-paid supplier charge | `trip_invoice_save` with REQUEST_AUTHORIZATION |
| Mark a fee/payment received (check, wire, cash) | `client_payment_configuration_view saved_payment_methods` → `client_payment_mark_paid` |
| Refund | booking refund: `booking_refund_create`; client payment refund: `client_payment_refund`; whole trip: `trip_cancel` with `tripItemRefunds` |
| Commission owed/received | `commission_search`; commission invoice PDF to supplier: `booking_supplier_invoice_download` |
| To-dos | `task_search` / `task_save` / `task_delete` (date reminders are excluded by default) |
| Tags | `client_tags_set` / `trip_tags_set` (full list replace) |
| Group / company membership | `group_*`, `corporate_client_*` |
| Advisor payout / statements | `statement_summary_list` → `statement_recipient_search` → `statement_user_view` / `statement_agency_recipient_list` |
| Attach a file | `attachment_create` (≤256 KB inline) or `attachment_upload_url_create` → PUT → `attachment_create` |
| Something in the MCP is confusing/missing | `feedback_submit` (no secrets, no customer PII) |

## Reading data well

- **`id` short-circuits everything.** Passing `id` returns that one record and ignores every other filter. Public IDs (e.g. `J37CFX8HJ`) work wherever the description says "UUID or public ID", but write tools generally require the UUID.
- **Filter server-side, don't page and filter in your head.** Date windows (`startDate_gte/_lt`, `dueAt_lt`, `createdAt_gte`…), `status_in`, `stage_in`, `tag`, `clientId`, `tripId`. Timestamps need an ISO 8601 offset (`2026-11-01T00:00:00Z`); trip/booking start/end *values* are civil dates (`2027-11-07`).
- **Trim payloads.** Use `fields=a,b,c` to return only what you need and `expand=` for relations (non-transitive: expanding `trip` does not also expand the trip's client). `count=false` skips the total-count query.
- **Pagination.** Two modes, mutually exclusive: offset (`page` 0-based ≤400, `pageSize` ≤500) or cursor (`cursor` from `pagination.next_cursor`, `limit` ≤500). Ranked free-text `q` searches are served from offset pages automatically. Don't combine a custom `sort` with a cursor issued by a different sort. Loop until `has_more` is false when the user wants "all"; otherwise say you only looked at the first N of `total_count`.
- **Free-text minimums:** trip `q` ≥3 chars, client_payment `q` ≥3, supplier `q` ≥2. Client `q` multi-word means every word must match first or last name; it also matches email substring and phone digits.
- **Booleans are strings** in filters: `"true"` / `"false"`.
- **Stage vs status.** `trip_search status_in` filters `active|canceled|locked`. The pipeline "Status" label (Lead, Planning, Booked…) is a *stage*: filter with `stage_in` (IDs from `trip_stage_list`), read with `expand=configuredStage`. Date-derived stages (Packing, Traveling, Traveled…) shown by `expand=stage` can't be filtered by ID, so use date filters instead.
- **Tasks:** by default `task_search` returns actionable to-dos and **excludes** birthday/anniversary/passport reminders. Those are auto-generated and are never "overdue". Never report them as outstanding. Use `isDateReminder=true` or `type=` only when asked about them.

## Writing data well

- **Partial updates:** include only the fields the user asked to change. `null` clears a nullable field; omission leaves it unchanged (except the replace-style blocks noted in rule 5).
- **Generated IDs:** create operations need a client-generated UUIDv4 `id` in several places (booking, client payment, invoice line items/sub-items, supplier payment entries). Use `scripts/new_uuid.py` or generate a valid v4. Reuse the same id when retrying the same create: it makes the call idempotent (a collision returns 409 `ID_ALREADY_EXISTS`).
- **Money format:** decimal **strings** in major units: `{"amount": "266.00", "currency": "USD"}`. Percentages and `exchangeRate` are numbers. Currencies are ISO 4217. For client payments/invoices use the org home currency unless the user names another, and it must be in `clientPaymentCurrencies`.
- **Date/time formats** differ by field (civil date vs `HH:MM` vs ISO local vs UTC-`Z`). See `references/booking-components.md`; run `scripts/lint_payload.py` on anything non-trivial.
- **Locked trips** can't be edited, cancelled, reinstated, or deleted (stage changes are the exception). ARC bookings have restrictions on refunds/voids and are handled in the ARC dashboard.
- **After writing,** re-read or use the returned record to report the outcome (names, dates, totals, `appUrl`). For financial writes report the amounts the system returned, not your own arithmetic.

## Working style

- Lead with the result, then the one or two things the user must decide. Offer a recommended default and say what it implies.
- Use human names and links, not UUIDs. Say "Created trip *Lisbon Spring 2027* (link)" rather than printing IDs.
- When a tool rejects a request, read the error, fix the specific problem, and explain it plainly. Don't loop on retries or "work around" guardrails (e.g. don't flip a booking to client-paid just to dodge an agency-schedule mismatch). See `references/gotchas-and-errors.md`.
- If a capability isn't exposed (e.g. creating commission records, discovering service-provider IDs, supplier-badge IDs, commission group IDs), say so, and consider `feedback_submit` if it blocked the task.
