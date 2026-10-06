# ID resolution, versions (`ifMatch`), and generated IDs

Almost every TripSuite write takes at least one UUID. The tool schemas tell you the *source* of each ID (a lookup tool + result path). This page consolidates those chains so you don't have to re-derive them.

## Contents
0. [Resolution policy: UUID first, search second, confirm after searching](#0-resolution-policy-uuid-first-search-second-confirm-after-searching)
1. [Lookup chains](#1-lookup-chains)
2. [IDs you generate yourself](#2-ids-you-generate-yourself)
3. [IDs that are not discoverable](#3-ids-that-are-not-discoverable)
4. [The `ifMatch` / `etag` pattern](#4-the-ifmatch--etag-pattern)
5. [Which writes need `ifMatch`](#5-which-writes-need-ifmatch)
6. [User ID vs advisor ID vs agency ID](#6-user-id-vs-advisor-id-vs-agency-id)

---

## 0. Resolution policy: UUID first, search second, confirm after searching

Decision order for **every** record you need (client, trip, booking, supplier, group/company, advisor, stage, destination, fee type…):

1. **Is a UUID available?** (user supplied it, it appears in an `appUrl` like `…/trips/<uuid>`, it came from an earlier tool result, or you already confirmed it this conversation.) → Use it. Fetch by `id=` to read, or to obtain the `etag` for a write. Done: no search, no extra confirmation.
2. **Is a public ID available?** (e.g. `J37CFX8HJ`.) → Exact-id fetch with `id=<publicId>`; take `data.id` (the UUID) for writes and say who/what it resolved to.
3. **Otherwise you only have a name/email/phone/confirmation number/description** → search with the narrowest filter, then **confirm the result with the user before using it.**

Confirmation message pattern (name + contact + one distinguishing detail + clear question):

```
I found Jane Doe (jane.doe@example.com · advisor: you · 3 trips, next: Lisbon May 2027).
Is that the right client?
```
- 1 match → still confirm. N matches → list 2–4, ask which. 0 → say what you searched; offer looser search / inactive records / create.
- Batch: resolve everything the task needs, then ask once, together with the plan (one "yes" confirms the records *and* the action).
- After a "yes", remember the UUID for the conversation; refer to the record by name; don't re-search or re-confirm.
- A UUID that fails to resolve is reported to the user; **never silently replaced by a name search.**
- If the UUID and the user's description disagree (e.g. different email), trust the UUID and flag the mismatch.

Where this applies per entity (search tool, what to show in the confirmation):

| Entity | Search with | Show in confirmation |
|---|---|---|
| Client | `client_search` (`email` exact first, then `q`/`*_like`) | name, email/phone, advisor, trip count |
| Trip | `trip_search` (`q`, `clientId`, dates) | name, client, dates, destination, status |
| Booking | `booking_search` (`q`=confirmation #/PNR, `tripId`) | supplier, confirmation #, dates, total, trip |
| Supplier | `supplier_search name=` exact, then `q` | name, type, city |
| Group / company | `group_search` / `corporate_client_search` | name, member count |
| Advisor | `user_search` | name, agency |
| Stage / destination / fee type / payment method | `trip_stage_list` / `destination_search` / config views | the exact label, e.g. "Booked", "Lisbon, Portugal" |

> UUIDs are for **tool calls only**. When you talk to the user, translate every ID back to a name or label (see `SKILL.md` → "Showing records to the user").

---

## 1. Lookup chains

| You need | Get it from | Result path | Notes |
|---|---|---|---|
| `clientId` / client `id` | `client_search` | `data[].id` | Disambiguate with the user if >1 match. |
| `tripId` | `trip_search` | `data[].id` | |
| `bookingId` | `booking_search` | `data[].id` | Empty ≠ trip doesn't exist (trips with no bookings don't appear). |
| Component `id` / segment `id` | `booking_search id=<booking> expand=components` | `data.components[].id`, `data.components[].air.segments[].id`, `data.components[].rail.segments[].id` | Segment ids only when editing an existing segment; omit for new segments. |
| Payment-to-supplier id (`paymentToSupplierId`, invoice `bookingExpenseId`, attachment `booking_expense` entity id) | `booking_search id=<booking> expand=expenses` | `data.expenses[].id` | |
| Booking refund id (`refundId`) | `booking_search id=<booking> expand=refunds` | `data.refunds[].id` | |
| `clientPaymentId` | `client_payment_search` | `data[].id` | |
| Trip invoice id | `trip_invoice_search` | `data[].id` | |
| Invoice line item / sub-item ids (for updates) | `trip_invoice_search id=<invoice>` | `data.lineItems[].id`, `data.lineItems[].subItems[].id` | Omit ids for new items. |
| `supplierId` / `parentId` / `associatedSupplierIds` | `supplier_search` | `data[].id` | Use exact `name` for existence checks. A booking's supplier may be a shared one not returned by search: fetch the booking by id and read `supplierId`. |
| `advisorId` (assignments, `assignedAdvisorId`, `assignedAdvisorIds`, splits) | `user_search` | `data[].agencies[].advisorId` | Under `user` access your own is `user_current_view.currentAdvisor.advisorId`. |
| `agencyId` | `user_search` | `data[].agencies[].agencyId` | Use the agency paired with the chosen advisor. Statements: `statement_recipient_search data[].recipient.agency.id`. |
| User id for statements | `statement_recipient_search` | `data[].recipient.user.id` | Own: `user_current_view.currentUserId`. |
| `user_search id=` | `user_search` | `data[].publicId` | |
| `corporateClientId` / `corporateGroupId` | `corporate_client_search` | `data[].id` | For a trip, use `clientId=<traveler>&isActive=true` to find the traveler's Company (or `isActive=true` alone if no traveler). |
| Leisure `groupId` | `group_search` | `data[].id` | |
| `stageId` / `stage_in` values | `trip_stage_list` | `data[].id` | Org-specific; confirm the exact label with the user if several look alike. |
| `destinationIds` | `destination_search` | `data[].id` (number) | One place per call. |
| `feeTypeId` | `client_payment_configuration_view {operation:"fee_types"}` | `data[].id` | |
| `clientPaymentMethodId` (mark-paid) | `client_payment_configuration_view {operation:"saved_payment_methods"}` | `data[].id` | Only where `supportsDirectPayment` is `false`. |
| Trip invoice `paymentMethodIds` | `trip_invoice_payment_method_list` | `data[].id` | Include all by default for REQUEST_PAYMENT; tell the advisor which were enabled. |
| Address id / loyalty program id | `client_profile_view` (sections `addresses` / `programs`) | `data.addresses[].id`, `data.programs.data[].id` | |
| `taskId` | `task_search` | `data[].id` | |
| Org id (for `organization_view`) | `user_current_view` | `organizationId` | The public org id works. |
| Attachment ids (for `booking_source_extract`) | `attachment_create` | `id` | File the source on the trip first. |

## 2. IDs you generate yourself

Where a schema says "Generate a new UUIDv4 value for this ID; do not look it up":

| Where | Field |
|---|---|
| `booking_save create_booking` | `booking.id` |
| `client_payment_save create` | `payment.id` |
| `trip_invoice_save create` | `invoice.lineItems[].id`, `invoice.lineItems[].subItems[].id` |
| `booking_financial_save add_payment_to_supplier` | `payment.id` (schedule entry), `payment.paymentId` (paid record; only valid with `paidDate`) |

Rules:
- Must be a valid **UUIDv4** (version nibble `4`, variant `8|9|a|b`). `scripts/new_uuid.py` prints some; or generate carefully yourself.
- **Idempotency:** if a create call errors ambiguously (timeout, network), *search first* to see whether it landed; if you retry, reuse the same id. A collision returns 409 `ID_ALREADY_EXISTS`, which on a retry of your own request means "it already worked".
- Don't reuse an id across different records.

## 3. IDs that are not discoverable

The connector exposes no lookup for these. Use them only if the **user** supplied them, otherwise omit the field:

- `serviceProviderId` on components (use `serviceProviderSupplierId` from `supplier_search` or `serviceProviderName` instead)
- `badgeIds` on suppliers
- `commissionGroupId` on `commission_search` (Supplier Payments group)
- `refundBillPaymentMethodId` / `billPaymentMethodId` (supplier-payment method *record* ids on refunds; `booking_payment_to_supplier_method_list` returns method values, not these ids)
- `externalClientId` (comes from an external client system), `interfaceId` (Sabre GDS vendor id), `voyageId` (from the cruise supplier / source doc)

## 4. The `ifMatch` / `etag` pattern

TripSuite uses optimistic concurrency. When you write to an existing record you must prove you saw its latest version.

1. **Fetch the record by exact `id`** (e.g. `trip_search id=<uuid>`). The response is `{ "etag": "W/\"updatedAt:2026-10-02T21:02:46.471Z\"", "data": { … } }`.
2. **Copy the top-level `etag` string verbatim** into the write's `ifMatch` field, with quotes/`W/` prefix intact.
3. Write. If TripSuite says the record changed, **re-fetch**, look at what's different, reconsider whether your change still makes sense, and only then retry. Never retry with the stale value or "force" it.
4. Don't tell end users about etags or `ifMatch` unless they ask for implementation detail; just say you're checking the latest version.

Notes
- List/search rows do **not** carry the etag. You need an exact-id fetch even if you just listed the record.
- Do the fetch immediately before the write; for multi-step edits (e.g. update booking then add payment), re-fetch between writes because each write changes the version.
- Use the *same kind of fetch* the tool description names: booking financial changes want `booking_search` with `expand=expenses` or `refunds`; component changes want `booking_component_view`; personal profile changes want `client_profile_view`.

## 5. Which writes need `ifMatch`

**Need `ifMatch`** (fresh etag from an exact-id fetch):

| Write | Fetch the etag with |
|---|---|
| `client_save update_client`, `client_status_set`, `client_delete` | `client_search id=` |
| `client_profile_save` **only for the `personal` section** | `client_profile_view id= sections=[personal]` |
| `trip_save update_trip`, `set_stage`, `trip_cancel` (cancel/reinstate), `trip_delete` | `trip_search id=` |
| `booking_save update_booking`, `booking_cancel`, `booking_void_or_delete`, `booking_refund_create`, `booking_financial_save` (all 3 ops), `booking_payment_to_supplier_delete` | `booking_search id= [expand=expenses,refunds]` |
| `booking_component_save update_component`, `booking_component_delete` | `booking_component_view id=` |
| `client_payment_save update`, `client_payment_mark_paid`, `client_payment_refund`, `client_payment_void_or_delete` | `client_payment_search id=` |
| `trip_invoice_save update`, `trip_invoice_duplicate`, `trip_invoice_delete` | `trip_invoice_search id=` |
| `supplier_update` | `supplier_search id=` |
| `group_save update`, `group_delete`, `corporate_client_save update`, `corporate_client_delete` | `group_search id=` / `corporate_client_search id=` |

**Do not take `ifMatch`:** all `create`/`add_*` operations, `client_tags_set`, `trip_tags_set`, `task_save` (create/update), `task_delete`, `group_save add_member/update_member`, `corporate_client_save add_member/update_member`, `group_member_delete`, `corporate_client_member_delete`, `client_profile_save` sections other than `personal`, `client_profile_item_delete`, `supplier_create`, `booking_component_save add_component/reorder_components`, attachments.

When unsure, check the schema: if `ifMatch` is in `required`, you need it.

## 6. User ID vs advisor ID vs agency ID

`user_current_view` example (shape):

```json
{ "accessLevel": "user",
  "organizationId": "1ZZIPJWV9",
  "currentUserId": "ad80a31e-…",
  "currentAdvisor": { "advisorId": "d78dea5c-…", "publicId": "AFFTWM0PU" },
  "guidance": "The user and advisor membership have different UUIDs." }
```

- **userId** = the person → statements (`statement_user_view.userId`).
- **advisorId** = that person's *membership in an agency* → who owns/assigned a trip, booking, client, task, group; booking commission splits.
- **agencyId** = the agency → `client_save create_client.agencyId` (defaults to the advisor's agency), split `agencyId`, agency statements.
- A person in multiple agencies has multiple `agencies[]` entries, each with its own `advisorId` + `agencyId`. Pick the pair that matches the record's agency.
- References on old records may point at deactivated advisors: use `user_search advisorId=<id> includeInactive=true`.
