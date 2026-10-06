# Gotchas, error patterns, and troubleshooting

## Contents
1. [Replace-vs-merge semantics](#1-replace-vs-merge-semantics)
2. [Error patterns and what to do](#2-error-patterns-and-what-to-do)
3. [Locked, ARC, and processed records](#3-locked-arc-and-processed-records)
4. [Search pitfalls](#4-search-pitfalls)
5. [Privacy and sensitive data](#5-privacy-and-sensitive-data)
6. [When something isn't possible](#6-when-something-isnt-possible)

---

## 1. Replace-vs-merge semantics

Sending a partial list/block here can **delete data**. Read first, send the complete desired set.

| Field | Behavior |
|---|---|
| `client_tags_set` / `trip_tags_set` `tags` | Full replace; omitted tags removed; `[]` clears all |
| `trip_save update_trip changes.destinationIds` | Full replace |
| `trip_invoice_save update` `lineItems`, `paymentMethodIds` | Full replace (an invoice still requesting payment can't have empty `paymentMethodIds`) |
| `booking_save update_booking changes.splits`, `additionalClientIds`, `udids` | Full replace; `[]` removes all |
| `client_payment_save update changes.udids` | Full replace of payment-level UDIDs |
| `supplier_update` `tags`, `badgeIds`, `destinationIds`, `associatedSupplierIds` | Full replace |
| `client_profile_save` `dates`, `health`, `preferences` | **Complete block: omitted fields inside are cleared** |
| `client_profile_save` `addresses` | Per address type replace; omitted types unchanged; each address must be complete |
| `booking_component_save reorder_components` | Must list the complete top-level order |
| Nullable fields (`null`) | Clears the value; omission leaves it unchanged |

## 2. Error patterns and what to do

| Symptom | Meaning | Action |
|---|---|---|
| Version/ifMatch conflict, "record changed" | Someone (or your earlier write) changed it | Re-fetch by exact id, re-read the diff, reconsider, retry with the new `etag`. Don't loop blindly. |
| 409 `ID_ALREADY_EXISTS` on create | Your generated id already exists | If it's a retry of your own request it probably succeeded: fetch by id. Otherwise generate a new UUIDv4. |
| 422 on AGENCY-paid booking create | No `expenses[]` or they don't sum to fare | Ask the user for the supplier payment schedule. Don't invent. |
| `AGENCY_SCHEDULE_MISMATCH` on `update_booking` | Re-pricing/converting while supplier payments disagree | `booking_financial_save update_payment_to_supplier`/`add_payment_to_supplier` to bring them in line, then re-send. Don't flip to client-paid as a workaround. |
| 409 `CLIENT_PAID_TS_PAYMENT_UNSUPPORTED` | TripSuite-funded method on a CLIENT-paying booking | Use a different method from `booking_payment_to_supplier_method_list`. |
| 403 `PAYMENT_METHOD_NOT_ENTITLED` | Org not entitled to that TS-funded method | Offer only methods the list returns. |
| Duplicate-email on `create_client` but search finds none | Existing client exists outside the user's visibility | Tell the user; ask an org admin to grant access or reassign. |
| Empty `booking_search` for a trip you know exists | Trips with no bookings don't appear | Use `trip_search`. |
| "3D Secure" setting rejected | `requireThreeDs:true` but org doesn't have it enabled | Omit it. |
| Missing-required-field validation | Schema requires something you omitted | Ask the user for that value rather than guessing. |
| Address rejected | Partial address or invalid country/state | Need address1+city+state+country (ISO name or code; state belongs to that country). Ask. |
| Segment time rejected | Numeric offset used | Use local wall time or `Z`. |
| Confirmed booking rejected: no confirmation number | `isConfirmed` defaults true | Get the number, or (only if the source says so) set `isConfirmed:false`. |
| `isCommissionable:true` rejected | No positive commission amount/percent | Source value, supplier default, or ask. |
| Can't delete/void | Processed, ARC, protected payout, >24h, paid commissions | Check `isDeletable`/`isVoidable`/`…Reasons` fields; explain; suggest the alternative (cancel, refund, ARC dashboard). |
| `client_payment_mark_paid` rejected | Method has `supportsDirectPayment:true` | Not a manual method; the real processor flow is required. |
| Date-format validation | Wrong format for that field | See `booking-components.md` §1. Lint the payload. |

Tool descriptions are the source of truth when this file and a tool disagree; re-read the schema.

## 3. Locked, ARC, and processed records

- **Locked trips** (`status: locked`): no edits, cancel, reinstate, delete, or tag changes. `set_stage` is allowed.
- **ARC bookings:** can't be refunded or voided via this MCP; refund changes blocked; handle in the ARC dashboard. Locked ARC weeks block deletion.
- **TripSuite-processed client payments:** financial fields locked; can't be voided; manual mark-paid not allowed; card refunds recorded pending.
- **Bookings with paid commissions** can't be voided.
- **Payments already sent for payout** can't be removed.
- Books close/statement close dates (`organization_view fields=booksCloseDate,statementsClosedAt`) may explain why historical edits are blocked.

## 4. Search pitfalls

- Passing `id` ignores all other filters, so don't pass both expecting a combined filter.
- `page` and `cursor` are mutually exclusive. A custom `sort` can't continue a cursor from another sort. Max `page` 400; use cursors for deep pagination.
- Free-text minimums (trip/client_payment `q` ≥3, supplier `q` ≥2).
- `endDate_*` on `booking_search` filters **check-out**, not trip end.
- `trip_search status_in` is `active|canceled|locked`; pipeline stage is separate (`stage_in`, `expand=configuredStage`).
- Boolean filters are strings.
- `expand` isn't transitive.
- A list `financials` expansion on bookings is only a commission summary; fetch a single booking for full financials.
- Results are permission-scoped: absence of a record in search isn't proof it doesn't exist org-wide.
- Supplier search lists only org suppliers; shared catalog suppliers appear only via a booking's `supplierId`.
- Date reminders are excluded from `task_search` by default.

## 5. Privacy and sensitive data

- `client_profile_view` returns health, passport, address and contact data: request only needed sections; summarize rather than dump; don't repeat unprompted.
- Invoice `memo` and `terms` are shown to the client: no internal notes, estimates, or sensitive profile details.
- `feedback_submit`: describe the *shape* of the problem. No names, emails, passport data, amounts tied to people, or credentials.
- Don't store sensitive details in task titles/descriptions or trip notes unless the user asks.
- Don't put credentials, card numbers, or full account numbers into any TripSuite field (payment method records are configured in the app, and the MCP never needs raw card data).

## 6. When something isn't possible

Not exposed through this MCP (as of writing): creating/reconciling commission records, discovering `serviceProviderId`, supplier badge ids, commission group ids, or supplier-payment method record ids; searching organizations; listing supplier payments across bookings (iterate bookings with `expand=expenses`); performing card-processor refunds or card payments; hard deletion; creating Corporate Programs; lead/reservation-import flows.

Say so plainly, offer the closest supported path (or point to the TripSuite app), and if it blocked the task use `feedback_submit` with category `missing_capability`.
