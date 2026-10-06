# Workflows (step-by-step recipes)

Each recipe lists the call order, what to ask the user, and what to report back. Adapt: skip steps whose answer is already known from the conversation. All recipes assume you've done the one-time orientation (§0).

## Contents
0. [Orient](#0-orient-once-per-conversation)
1. [Find and disambiguate a client](#1-find-and-disambiguate-a-client)
2. [Create a client](#2-create-a-client)
3. [Create a trip](#3-create-a-trip)
4. [Full picture of a trip](#4-full-picture-of-a-trip)
5. [Create a booking from a supplier document](#5-create-a-booking-from-a-supplier-document)
6. [Edit itinerary components](#6-edit-itinerary-components)
7. [Record, update, or settle a payment to a supplier](#7-record-update-or-settle-a-payment-to-a-supplier)
8. [Bill a client fee and invoice it](#8-bill-a-client-fee-and-invoice-it)
9. [Bill the client for agency-paid travel](#9-bill-the-client-for-agency-paid-travel)
10. [Client-paid booking: get authorization](#10-client-paid-booking-get-authorization)
11. [Mark a client payment received](#11-mark-a-client-payment-received-manual)
12. [Cancel a booking or a whole trip](#12-cancel-a-booking-or-a-whole-trip)
13. [Refunds](#13-refunds)
14. [Change pipeline Status / tags](#14-change-pipeline-status--tags)
15. [Update client profile data safely](#15-update-client-profile-data-safely)
16. [Tasks and reminders](#16-tasks-and-reminders)
17. [Groups and corporate accounts](#17-groups-and-corporate-accounts)
18. [Statements and payouts](#18-statements-and-payouts)
19. [Attach a file](#19-attach-a-file)
20. [Reporting recipes (read-only)](#20-reporting-recipes-read-only)

---

## 0. Orient (once per conversation)

> **Resolution policy for every recipe below:** use UUIDs you already have; search only when given just a name/email/description; **confirm search results with the user (batched with the plan) before using them.** See `id-resolution.md` §0.

1. `user_current_view` → note `accessLevel`, `currentUserId`, `currentAdvisor.advisorId`, `organizationId`.
2. If money is involved: `organization_view id=<organizationId> fields=homeCurrency,clientPaymentCurrencies,accountingBasis`.
3. `accessLevel === "organization"` → you must ask which advisor owns new trips/clients/tasks and look them up with `user_search`. `"user"` → defaults to the current advisor; only look up another advisor if the user names one.

## 1. Find and disambiguate a client

0. **UUID already known?** Use `client_search id=<uuid>` (or skip straight to the next step); no name search and no confirmation needed. Only search when you have just a name/email/phone.
1. `client_search q="first last"` (or `email=` exact, `phone_like=`). Add `expand=tags,tripCount` if helpful and `isActive=true` unless history matters.
2. 0 results → try looser (`lastName_like`), then say so; offer to create. **1 → still confirm with the user** ("I found Jane Doe, jane@…, 3 trips. Right client?"). >1 → show candidates (name, email, advisor/company, trip count) and ask. Don't proceed until they say yes.
3. Remember `data[].id`. Don't call `client_profile_view` unless you need profile sections.

## 2. Create a client

1. `client_search` by email (exact) and by name to avoid duplicates. If one exists, confirm "use existing?"
2. The schema only strictly requires `operation`, but always collect first and last name. Optional: email, phone, preferredName, company. Advisor: omit under `user` access; under `organization` access choose via `user_search` → `agencies[].advisorId` (+ matching `agencyId`).
3. `client_save {operation:"create_client", firstName, lastName, email, phone, …}`.
4. Duplicate-email error but your search found nothing → the existing client is outside the user's visibility. Tell the user to ask an org admin to grant access/reassign; don't create a workaround.
5. Anything beyond basics (middle name, address, birthday, preferences, loyalty, emergency contact) → `client_profile_save` (see §15).

## 3. Create a trip

1. **Client:** §1/§2 to get `primaryClientId` (UUID if known, else search + confirm) (leisure) or, for corporate, the Company (`corporate_client_search clientId=<traveler> isActive=true`; or `isActive=true` alone if anchoring on the company with no traveler).
2. **Travel type:** `leisure` or `corporate`. If not explicit or clear from context, **ask**.
3. **Destinations (required):** for each place the user named, `destination_search q="…"` (one per call). Prefer the most specific match (city over country); ask when ambiguous. If the user gave no destination, ask.
4. **Duplicate check:** `trip_search clientId=<id> status_in=active` (add `startDate_gte`/`_lt` around the dates ±30 days). If trips overlap or fall within 30 days of the requested dates, show up to three and ask whether to reuse one (and adjust dates) before creating another. Never reuse a canceled/removed trip.
5. **Create:** `trip_save {operation:"create_trip", trip:{name, travelType, destinationIds, primaryClientId | corporateClientId, startDate, endDate, notes?, advisorId?}}`. `type` stays `"standard"`.
6. **Optional:** set stage (§14), tags, additional travelers (done on bookings via `additionalClientIds`).
7. **Report:** trip name, dates, destinations, advisor, `appUrl`.

Name convention: if the user gives none, propose `"<Destination> – <Client last name> (<Month Year>)"` and say you chose it.

## 4. Full picture of a trip

Run these in parallel after you have the trip id:
- `trip_search id=<id> expand=primaryClient,advisor,additionalClients,tags,configuredStage`
- `booking_search tripId=<id> fields=id,publicId,confirmationNumber,status,startDate,endDate,totalAmount,payingEntity,supplierId expand=supplier`
- `client_payment_search tripId=<id> fields=id,subject,invoiceFor,status,total,totalCharged,dueDate,paidAt`
- `trip_invoice_search tripId=<id>`
- `task_search tripId=<id> isCompleted=false`

Summarize: who/where/when, bookings and totals by status, what the client has paid vs owes, open tasks. Flag anything inconsistent (e.g. AGENCY-paid booking with no client payments; unpaid payment past due).

## 5. Create a booking from a supplier document

The highest-risk write. Do it in this order:

1. **Trip:** make sure it exists and is not locked/cancelled (`trip_search`). Don't rely on `booking_search` for this. If the trip doesn't exist, create it first (§3).
2. **Preserve the source:** if the user supplied a PDF/image, file it on the trip (`attachment_create entityType:"trip"`) so extraction can read it and advisors can see it. If it's pasted text, pass it verbatim.
3. **Extract:** `booking_source_extract {text and/or attachmentIds}`. Read the **coverage inventory and issues**: recover missing arrangements, split grouped visits, resolve conflicting/optional choices (don't treat optional/alternative items as confirmed). Don't re-extract unchanged sources.
4. **Supplier:** `supplier_search name="<exact>"` → if none, `supplier_search q=` for near matches; if truly absent, `supplier_create` (after a duplicate check). Take `supplier.id`.
5. **Resolve the required decisions**, asking for any not stated in the document:
   - `payingEntity` (CLIENT / AGENCY). Never assume.
   - `isCommissionable` and commission amount/percent/due date (see `money-flows.md` §7). Don't infer from supplier defaults.
   - `isConfirmed`: default confirmed. Set `false` only if the source says proposed/quote/hold. A confirmed booking **needs** `confirmationNumber`; never invent one.
   - If AGENCY-paid: the supplier payment schedule (`expenses[]`: amount, method, due date, paid?). Call `booking_payment_to_supplier_method_list` first.
   - Client (defaults to trip primary) and any additional travelers.
6. **Build the request:** preserve the extracted components and their order (`sortOrder`), identifiable components only (no placeholders), `bookedDate` from the source, `totalAmount` as the sale total in the booking currency, `taxesAndFees`, `baseFare`, `notes`. Generate `booking.id` (UUIDv4). Omit `exchangeRate` unless the user supplied one. See `booking-components.md` for per-type fields and formats.
7. **Lint (optional but recommended):** write the request to a file and run `python scripts/lint_payload.py <file>`.
8. **Summarize before writing** when anything was inferred or the money is large: supplier, dates, total + currency, paying entity, commission, payment schedule, components list. Then `booking_save {operation:"create_booking", booking:{…}}`.
9. **Verify:** `booking_search id=<new id> expand=components,expenses` and report what was created (and anything from the extraction you could not place).
10. **Next steps to offer:** a Trip Invoice (authorization or payment request), client payments if AGENCY-paid, a task to follow up on commission or final payment.

Mistakes to avoid: summarizing the document before extraction; creating a booking per component of the same reservation; putting hotel perks (e.g. Virtuoso amenities) on a separate component (they belong on the hotel component's `hotel.amenities`); duplicating supplier deposits as client payments.

## 6. Edit itinerary components

1. `booking_search id=<booking> expand=components` → find the component + its `id` (and the booking etag).
2. **Add:** `booking_component_save {operation:"add_component", bookingId, component:{type, …}}`. No etag needed.
3. **Update:** `booking_component_view id=<componentId>` (→ `etag`) → `booking_component_save {operation:"update_component", bookingId, componentId, ifMatch, changes:{type:"hotel", …only changed fields…}}`. `changes` must include `type`. To edit one air/rail segment, include that segment with its `id`.
4. **Reorder:** `{operation:"reorder_components", bookingId, componentIds:[…complete top-level order…]}`.
5. **Remove:** confirm → `booking_component_view` (etag) → `booking_component_delete {id, ifMatch}`.
6. Component edits don't change money. If the sale price/dates changed, also update the booking (`booking_save update_booking`).

## 7. Record, update, or settle a payment to a supplier

*(Money OUT. Applies to both CLIENT- and AGENCY-paid bookings.)*

1. `booking_search id=<booking> expand=expenses` → get existing entries (`data.expenses[].id`), booking `etag`, and `payingEntity`.
2. `booking_payment_to_supplier_method_list` → offer **only** what it returns (in order). Ask: which method, which due date, already paid?
3. **Add:** `booking_financial_save {operation:"add_payment_to_supplier", bookingId, ifMatch, payment:{amount:{amount,currency}, dueDate:"YYYY-MM-DD", paymentMethod, subject:"Hotel deposit", [paidDate], [isPaidAtCheckout]}}`. Omit `paidDate` for a pending schedule entry. Use `isPaidAtCheckout:true` when it settles at check-out (paid date derived from check-out).
4. **Settle an existing entry:** `update_payment_to_supplier {paymentToSupplierId, changes:{paidDate:"YYYY-MM-DD"}}`. **Revert to pending:** `paidDate:null` (this voids the paid record).
5. **Remove:** confirm → `booking_payment_to_supplier_delete {id:<booking>, paymentToSupplierId, ifMatch}` (also voids its paid record; not allowed if already sent for payout).
6. AGENCY-paid: schedule must total the fare. After any change, re-read `expenses` and confirm the total still equals the booking fare.
7. Re-fetch between consecutive writes: each write changes the booking's etag.

## 8. Bill a client fee and invoice it

1. `organization_view` for the home currency (if not already known).
2. `client_payment_configuration_view {operation:"fee_types"}` → pick the category (ask if unclear).
3. `client_payment_save {operation:"create", payment:{id:<uuid>, tripId, clientId, subject:"Planning fee", invoiceFor:"FEES", feeTypeId, total:{amount:"250.00", currency:<home>}, dueDate:"YYYY-MM-DD"}}`. Add `clientPaysProcessingCosts:true` only if asked; `processingCostPct` only if the user states a rate.
4. Report `totalCharged` **from the response**.
5. To send it to the client: `trip_invoice_payment_method_list` → `trip_invoice_save create` with a line item `{clientPaymentId, subItems:[{clientAction:"REQUEST_PAYMENT"}]}` and all returned `paymentMethodIds` (tell the advisor which). Memo/terms optional, client-facing wording only.

## 9. Bill the client for agency-paid travel

Only when the booking's `payingEntity` is `AGENCY`.
1. Confirm client-payment currency and the installment plan (amounts + due dates).
2. One `client_payment_save create` per installment with `invoiceFor:"TRIP"`, `subject` like "Cruise deposit", `dueDate`.
3. One `trip_invoice_save create` including each as `REQUEST_PAYMENT` line items (order them), `paymentMethodIds` = all from `trip_invoice_payment_method_list`.
4. Never create TRIP client payments for CLIENT-paid bookings (see §10).

## 10. Client-paid booking: get authorization

1. `booking_search id=<booking> expand=expenses` → the `expenses[].id` for the charge(s) the client should approve.
2. `trip_invoice_save create` with `paymentMethodIds: []`, one line item `{bookingId}` and sub-items `{clientAction:"REQUEST_AUTHORIZATION", bookingExpenseId:<id>}`. No client payment is created.
3. Mention that this collects no money for the agency; the advisor submits the supplier charge with the client's method.

## 11. Mark a client payment received (manual)

1. `client_payment_search id=<id> fields=status,total,totalCharged,supportsDirectPayment,directPaymentIneligibilityReasons,isVoidable` → confirm it's unpaid and what's expected.
2. `client_payment_configuration_view {operation:"saved_payment_methods"}` → choose a method with `supportsDirectPayment:false` (check/wire/cash style). **Never** for TripSuite CC/ACH Processing: that must go through the real processor journey. Say so if the user asks.
3. Confirm method + received date → `client_payment_mark_paid {id, ifMatch, body:{clientPaymentMethodId, paidAt:<ISO datetime with offset>}}`.

## 12. Cancel a booking or a whole trip

**Booking:** `booking_search id=` (status, payments, commission) → explain: cancel doesn't void payments or clear commission; if it's the last active booking the trip cancels → get a yes → `booking_cancel {id, ifMatch}`. If the user actually wants the financials cleared, that's **void**, a different, stronger action.

**Trip:**
1. `trip_search id=` (check `status`; `locked` can't be cancelled).
2. List active bookings and active client payments that will cancel; ask about refunds (amounts, methods, dates) and whether supplier-side refunds are known.
3. Get an explicit yes.
4. `trip_cancel {operation:"cancel", tripId, ifMatch, cancellation?:{tripItemRefunds:[…]}}`.
5. Report what was cancelled; remind that card refunds are pending/manual.
6. **Reinstate:** `trip_cancel {operation:"reinstate", …}` only restores trip status; bookings/client payments stay cancelled.

## 13. Refunds

- **Supplier gave the agency money back / booking value reduced:** `booking_search id= expand=refunds,financials` → `booking_refund_create {id, ifMatch, body:{amount:{amount,currency}, baseFareAmount?, estimatedCommissionAmount?, penalty?, paymentMethod?, refundedAt?}}`. Fix later with `booking_financial_save update_refund`. Not for ARC.
- **Client gets money back for a paid payment:** `client_payment_refund {id, ifMatch, body:{refundedAmount:"…", refundPaymentMethod?, refundIssuedAt?, refundedProcessingCostAmount?}}`. Payment must be paid. Card refunds are recorded pending; the processor reversal is manual.
- Always confirm amounts and which refund type with the user; report the resulting totals from the response.

## 14. Change pipeline Status / tags

- **Status:** `trip_stage_list` → match the user's wording to exactly one stage (ask if two look alike) → `trip_search id=` (etag) → `trip_save {operation:"set_stage", tripId, ifMatch, stageId}`. Works on locked trips. If the trip is linked to a lead, the lead's stage syncs.
- **Tags:** `trip_search id= expand=tags` (or `client_search id= expand=tags`) → `trip_tags_set` / `client_tags_set {id, body:{tags:[…existing…, "New"]}}`. **Full replace**: omitted tags are removed. New names create new org-wide tags (check spelling/case against existing tags first; names match case-insensitively).

## 15. Update client profile data safely

1. Decide the minimum sections needed. `client_profile_view {id, sections:[…]}` (sensitive; don't echo more than needed).
2. **Blocks are replace-style:**
   - `dates`, `health`, `preferences`: omitted fields inside a provided block are **cleared**. To add "shellfish" to allergies, send the **entire** `health` block with the existing `allergies` + the new one, plus existing `dietaryRestrictions`, `mobilityRestrictions`, `notes`.
   - `addresses`: per address type (`primaryDetails`, `secondaryDetails`, `billingDetails`, `businessDetails`) replace; types you omit are untouched. Every address you supply must be complete (address1, city, state, country (ISO)). Ask for missing parts.
   - `loyaltyPrograms`: `create` / `update {programId, changes}`; `programNotes` for notes shared across programs.
   - `personal` (gender, pronouns, secondary email/phone, emergency contact, referral source, private notes, external client id): its fields are nullable (`null` clears), and unlike `dates`/`health`/`preferences` the schema does **not** say omitted fields are cleared, so send only the fields you're changing. Because the semantics aren't spelled out, re-view the section afterwards and confirm nothing else changed. It requires `ifMatch` (etag from a fresh `client_profile_view` of that section) and makes exactly one write attempt.
3. `client_profile_save {clientId, <sections>, ifMatch (only with personal)}`. The result reports success/failure **per section**; surface any failure.
4. Remove an address or loyalty program: `client_profile_item_delete` after confirmation.
5. Primary email/phone, names, advisor, company → `client_save`, not here.

## 16. Tasks and reminders

- **Create:** link to a trip and/or client (required). `task_save {operation:"create", task:{title, description?, dueAt?, remindAt?, tripId?, clientId?, assignedAdvisorIds?}}`. Dates are ISO 8601 with offset. Under `organization` access you must supply `assignedAdvisorIds`.
- **Complete/edit:** `task_save {operation:"update", taskId, changes:{isCompleted:true}}`. No `ifMatch`.
- **"What's overdue/due?"** → `task_search isCompleted=false dueAt_lt=<now ISO> sort=dueAt` (add `assignedAdvisorId` for a person). Date reminders (birthdays, anniversaries, passport expirations) are excluded by default and are never overdue.
- **"Upcoming birthdays/passport expirations"** → `task_search isDateReminder=true type=BIRTHDAY remindAt_gte=… remindAt_lt=…`.
- Delete: confirm → `task_delete` (load its schema via tool search first).

## 17. Groups and corporate accounts

- Find: `group_search q=` / `corporate_client_search q=` (`expand=members,memberCount`).
- Create: `group_save create` / `corporate_client_save create` (corporate needs `name` and `sourcedBy`), then `add_member` for each client (`isPrimary:true` makes others non-primary).
- Rename/update: fetch exact (etag) → `update`.
- Remove a member: confirm → `group_member_delete` / `corporate_client_member_delete` (re-adding restores).
- Delete the whole group/company: confirm; it removes memberships and detaches from trips.
- A **corporate trip** is anchored on a Company: use `corporate_client_search clientId=<traveler> isActive=true`.

## 18. Statements and payouts

1. Determine the period: `statement_summary_list startDate endDate` (collect **all pages**). Each returned `startDate` is one statement period. Payouts are **not prorated**: if the user's range cuts through a period, include the whole period and tell them the actual bounds.
2. Own statement: `statement_user_view userId=<currentUserId> startDate=<period start>`; add `type: bookings | trips | expenses` for detail (page through all rows; `pageSize` ≤ 500).
3. Others (needs admin/accountant visibility): `statement_recipient_search startDate=` → `recipient.user.id` → `statement_user_view`. Agency view: `statement_recipient_search` → `recipient.agency.id` → `statement_agency_recipient_list`.
4. For a multi-period total, sum the per-period figures yourself and show the breakdown by period.

## 19. Attach a file

- **Small (≤256 KB):** `attachment_create {entityType, entityId, name:"Confirmation.pdf", contentType:"application/pdf", contentBase64}`. The bytes pass through you, so only do this when you actually have them (e.g. a file the user uploaded to the conversation).
- **Large:** `attachment_upload_url_create {filename, contentType}` → HTTP `PUT` the bytes to `writeUrl` with the **same** `Content-Type` → `attachment_create {entityType, entityId, name, externalFilename}`. If you can't perform a PUT, tell the user to upload in the app.
- `entityType` ∈ `trip | booking | client | supplier | booking_expense` and `entityId` must be that type's id.
- Treat attachments (passports, IDs) as sensitive. File to the minimum appropriate record.

## 20. Reporting recipes (read-only)

For analysis and multi-step reporting (revenue, commission, pipeline, supplier reviews, ambiguity handling, response templates) see `workflow-patterns.md`. Quick lookups:

| Question | Calls |
|---|---|
| Upcoming departures next 30/60 days | `trip_search startDate_gte=<today> startDate_lt=<today+N> status_in=active sort=startDate expand=primaryClient,advisor` |
| Trips by pipeline status | `trip_stage_list` → `trip_search stage_in=<ids>` (use `expand=configuredStage`) |
| Trips returning this month | `trip_search endDate_gte=… endDate_lt=…` |
| A client's history | `trip_search clientId=` + `client_payment_search clientId=` |
| Unpaid client payments due soon | `client_payment_search status_in=active dueDate_lt=<date> sort=dueDate fields=subject,total,totalCharged,dueDate,clientId,tripId` |
| Supplier payments coming due | `booking_search status_in=confirmed expand=expenses startDate_gte=…` then filter `expenses` by due date and unpaid (no direct expense search exists) |
| Commission outstanding by supplier | `booking_search supplierId= fields=estimatedCommission,commissionDueDate,commissionStatus,supplierCommissionState,commissionPaidAt,totalAmount` |
| Commission received | `commission_search status_in=active receivedDate/reconciledAt window` |
| Bookings missing confirmation numbers | `booking_search status_in=pending` (and inspect `confirmationNumber`) |
| Advisor workload | `trip_search` has no advisor filter. Use `client_search assignedAdvisorId=` / `task_search assignedAdvisorId=`; a trip's advisor shows via `expand=advisor` |

When a report needs more than ~3 pages of results, tell the user the scale (`total_count`) and either summarize with aggregates you compute while paging or ask whether they want the full list. Use `count=false` on subsequent pages.
