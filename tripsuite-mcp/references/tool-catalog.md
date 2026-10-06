# TripSuite tool catalog

Every tool, grouped by domain. Bare names are used here; most clients prefix them `mcp__TripSuite__`.

**Legend**
- 🔎 read-only  ✍️ create/update  🗑️ delete (reversible hide)  ⚠️ cascades / financial / hard to reverse
- `ifMatch` = needs the `etag` from a fresh exact-id fetch (see `id-resolution.md`)
- "Returns IDs for…" = what you can feed into other tools from this tool's output

## Contents
1. [Context & reference data](#1-context--reference-data)
2. [Clients](#2-clients)
3. [Groups & corporate accounts](#3-groups--corporate-accounts)
4. [Trips](#4-trips)
5. [Bookings & itinerary components](#5-bookings--itinerary-components)
6. [Suppliers](#6-suppliers)
7. [Client payments (money IN from clients)](#7-client-payments-money-in-from-clients)
8. [Trip invoices (client-facing documents)](#8-trip-invoices-client-facing-documents)
9. [Commissions (money IN from suppliers)](#9-commissions-money-in-from-suppliers)
10. [Tasks](#10-tasks)
11. [Attachments](#11-attachments)
12. [Statements (advisor/agency payouts)](#12-statements-advisoragency-payouts)
13. [Feedback](#13-feedback)

---

## 1. Context & reference data

| Tool | Purpose / key args | Notes |
|---|---|---|
| `user_current_view` 🔎 | No args. Returns `accessLevel` (`user`\|`organization`), `organizationId`, `currentUserId`, `currentAdvisor.{advisorId,publicId}`. | Call once at the start. `organization` access has no represented person, so advisor-bearing writes need an explicit advisor. |
| `organization_view` 🔎 | `id` (use `organizationId` from `user_current_view`), `fields=homeCurrency,clientPaymentCurrencies,accountingBasis,booksCloseDate,statementsClosedAt,paymentInstructions…` | Source of truth for default currency. Verified to accept the public org ID. |
| `user_search` 🔎 | `q`-style filters: `advisorId`, `agencyId`, `includeInactive`, `fields`, `id` (use `data[].publicId`). | Returns `data[].agencies[].advisorId` and `.agencyId`. Employees see their agency; contractors see only themselves. `includeInactive=true` to resolve former advisors on old records. |
| `destination_search` 🔎 | `q` (one place per call). | Returns numeric `data[].id` for `destinationIds`. Prefer city over country; ask when several places share the name ("Paris, TX"). Global reference data. |
| `trip_stage_list` 🔎 | `includeRemoved` (only to decode old records). | Returns `{id,name}` for the org's pipeline stages (e.g. Lead/Planning/Booked/Declined/Lost; names vary per org). |
| `client_payment_configuration_view` 🔎 | `request:{operation:"fee_types"}` or `{operation:"saved_payment_methods"}`. | `fee_types` → `feeTypeId` for FEES payments. `saved_payment_methods` → `clientPaymentMethodId` for manual mark-paid (only where `supportsDirectPayment:false`). |
| `trip_invoice_payment_method_list` 🔎 | No args. | IDs for `trip_invoice_save.paymentMethodIds`. Include all by default when any item is REQUEST_PAYMENT. |
| `booking_payment_to_supplier_method_list` 🔎 | No args. | The methods this org may use for payments **to** suppliers. Always call before recording one; TripSuite-funded methods missing from the list are not permitted. |

## 2. Clients

| Tool | Purpose / key args | Notes |
|---|---|---|
| `client_search` 🔎 | `id`, `q`, `email` (exact), `phone_like` (digits-only match), `firstName_like`, `lastName_like`, `assignedAdvisorId`, `corporateGroupId`, `isCorporate`, `isActive`, `tag`, `expand=assignedAdvisor,corporateGroup,tripCount,tags`, `fields`… | Basic identity + primary contact only. Returns `data[].id` (clientId everywhere). No sensitive profile data. |
| `client_save` ✍️ | `request:{operation:"create_client", firstName, lastName, email, phone, preferredName, company, assignedAdvisorId, agencyId}` or `{operation:"update_client", clientId, ifMatch, …changes}` | `ifMatch` on update. Names, preferred name, primary email/phone, company, advisor only. **Not** for middle name/prefix/suffix, addresses, health, dates, preferences, loyalty, secondary/emergency contacts (use `client_profile_save`). Reassigning the advisor also reassigns open tasks. Duplicate email → see gotchas. |
| `client_profile_view` 🔎 | `id`, `sections` (**required**, ≥1 of `personal,addresses,health,preferences,dates,programs,passports`) | Sensitive. Only requested sections returned. Passport images/files are never returned. Gives `data.addresses[].id` and `data.programs.data[].id`. The top-level `etag` here is the version for `personal` changes. |
| `client_profile_save` ✍️ | `clientId`, any of `personal`, `addresses`, `dates`, `health`, `preferences`, `loyaltyPrograms[]`, `programNotes`, plus `ifMatch` (**only** for `personal`) | Sections are written sequentially; the result reports per-section success/failure. **`dates`, `health`, `preferences` are complete blocks: omitted fields are cleared.** `addresses`: per type (`primaryDetails`, `secondaryDetails`, `billingDetails`, `businessDetails`) replace; each address must be complete (address1, city, state, country). `loyaltyPrograms`: `{operation:"create",program:{name,number,expirationDate}}` or `{operation:"update",programId,changes}`. `personal` makes exactly one write attempt. |
| `client_profile_item_delete` 🗑️ | `request:{operation:"delete_address",clientId,addressId}` or `{operation:"delete_loyalty_program",clientId,programId}` | Confirm first. IDs from `client_profile_view`. |
| `client_status_set` ✍️ | `id`, `ifMatch`, `body:{isActive}` | Inactive ≠ deleted; history preserved and still searchable. Prefer this for "retire/archive this client". |
| `client_tags_set` ✍️ | `id`, `body:{tags:[…]}` | **Full replace.** Read current tags with `client_search expand=tags` first. New names create new tags. `[]` removes all. No `ifMatch`. |
| `client_delete` 🗑️⚠️ | `id`, `ifMatch` | Confirm first. Fails for clients with active trips/bookings. |

## 3. Groups & corporate accounts

Leisure groups (families/friend circles) and corporate accounts (companies) are separate record types with parallel tools.

| Tool | Purpose / key args | Notes |
|---|---|---|
| `group_search` 🔎 | `id`, `q` (name substring), `clientId` (groups a client belongs to), `assignedAdvisorId`, `isActive`, `expand=members,contacts,assignedAdvisor,memberCount`, `fields` | |
| `group_member_list` 🔎 | `id` | Primary member first. |
| `group_save` ✍️ | `request` is one of: `{operation:"create", group:{name,…,sourcedBy:"ADVISOR"\|"AGENCY"}}`; `{operation:"update", groupId, ifMatch, changes}`; `{operation:"add_member", groupId, member:{clientId,isPrimary,relationship}}`; `{operation:"update_member", groupId, clientId, changes}` | `ifMatch` only for `update`. `isPrimary:true` demotes other primaries. Re-adding a former member restores them. |
| `group_member_delete` 🗑️ | `id` (group), `clientId` | Confirm first. Reversible by re-adding. |
| `group_delete` 🗑️⚠️ | `id`, `ifMatch` | Removes active memberships and detaches from trips. Confirm. |
| `corporate_client_search` 🔎 | like `group_search` plus `dkNumber` (exact) | Use `clientId`+`isActive=true` to find a traveler's Company when creating a corporate trip. |
| `corporate_client_member_list` 🔎 | `id` | |
| `corporate_client_save` ✍️ | `create` (name + `sourcedBy` required; billing client is auto-created), `update` (`ifMatch`), `add_member`, `update_member` | Mirrors group_save. Fields include `dkNumber`, `accountNumber`, `industry`, `fiscalYearStartMonth` (1–12). |
| `corporate_client_member_delete` 🗑️ | `id`, `clientId` | |
| `corporate_client_delete` 🗑️⚠️ | `id`, `ifMatch` | Removes memberships and detaches from trips. Confirm. |

## 4. Trips

| Tool | Purpose / key args | Notes |
|---|---|---|
| `trip_search` 🔎 | `id`, `q` (≥3 chars; matches name, public id, DK/account number, client, advisor, PNRs, booking ids, destinations), `clientId`, `startDate_gte/_lt`, `endDate_gte/_lt`, `createdAt_*`, `updatedAt_*`, `status_in` (`active,canceled,locked`), `stage_in`, `tag`, `expand=primaryClient,advisor,additionalClients,tags,stage,configuredStage`, `fields` | Use for any trip-level question. Exact fetch returns the `etag`. `fields` allows `destinations,notes,terms,groups,appUrl…`. |
| `trip_save` ✍️ | `request` is one of: **`create_trip`** `{trip:{name,travelType,destinationIds[],primaryClientId,corporateClientId,advisorId,startDate,endDate,notes,terms,type:"standard"}}`; **`update_trip`** `{tripId,ifMatch,changes}`; **`set_stage`** `{tripId,ifMatch,stageId}` | `name`, `travelType`, `destinationIds` required on create. Leisure needs `primaryClientId`; corporate needs `corporateClientId` (a corporate trip may omit the traveler). `destinationIds` on update replaces the whole list. Switching leisure↔corporate: `travelType` + `corporateClientId` (null for leisure; leisure needs a primary traveler). Locked trips: no edits except `set_stage`. Corporate *Programs* are not creatable here. |
| `trip_tags_set` ✍️ | `id`, `body:{tags:[…]}` | Full replace; read `trip_search expand=tags` first. Locked trips can't change. |
| `trip_cancel` ⚠️ | `request:{operation:"cancel", tripId, ifMatch, cancellation?:{tripItemRefunds:[…]}}` or `{operation:"reinstate", tripId, ifMatch}` | Cancel cascades to **all active bookings and active client payments** and can record refunds in the same call. `tripItemRefunds` entries are `{type:"BOOKING", itemId (booking id), amount, …}` or `{type:"CLIENT_INVOICE", itemId (client payment id), amount, …}`. Reinstate only reactivates the trip. |
| `trip_delete` 🗑️⚠️ | `id`, `ifMatch` | Confirm first. Locked trips can't be removed. If the trip was real/booked, prefer `trip_cancel`. |

## 5. Bookings & itinerary components

A **booking** is one supplier reservation on a trip; **components** are the itinerary pieces inside it.

| Tool | Purpose / key args | Notes |
|---|---|---|
| `booking_search` 🔎 | `id`, `q` (confirmation #, public id, PNR, supplier, client, advisor), `tripId`, `clientId`, `supplierId`, `status_in` (`canceled,voided,confirmed,pending`), `payingEntity`, `startDate_*` (= check-in), `endDate_*` (= **check-out**, not trip end), `expand=trip,primaryClient,supplier,advisor,additionalClients,splits,financials,commissions,expenses,refunds,components,attachments,tags,udids`, `fields` | Exact fetch + `expand=components,expenses,refunds` is how you get component IDs, payment-to-supplier IDs (`data.expenses[].id`), refund IDs, and the booking `etag`. On a *list*, `financials` returns only a commission summary; fetch one booking by id for full financials. |
| `booking_source_extract` 🔎 | `body:{text?, attachmentIds?[]}` | Smart-Import extraction of a supplier itinerary/invoice. **Creates nothing.** Read its coverage inventory and issues before `booking_save`. Don't re-run on unchanged sources. Attachments must already be filed on the trip (see `attachment_create`). |
| `booking_save` ✍️⚠️ | `request` is **`create_booking`** `{booking:{id,tripId,supplierId,startDate,endDate,totalAmount:{amount,currency},payingEntity,isCommissionable,…,components[],expenses[]}}` or **`update_booking`** `{bookingId,ifMatch,changes}` | See `money-flows.md` and `workflows.md` §Create booking. Creates the booking + all identifiable components + initial supplier payments atomically. `isConfirmed` defaults true and then requires `confirmationNumber`. AGENCY-paid requires `expenses[]` that total the fare. Later component edits → `booking_component_save`; later supplier payments/refunds → `booking_financial_save`. Voided bookings and locked ARC financials can't be changed. |
| `booking_component_view` 🔎 | `id` (component UUID), `fields` | Returns the component and its `etag` for edits/deletes. |
| `booking_component_save` ✍️ | `request` is **`add_component`** `{bookingId, component:{type,…}}`, **`update_component`** `{bookingId, componentId, ifMatch, changes:{type,…}}`, or **`reorder_components`** `{bookingId, componentIds:[…]}` | `type` ∈ `air,hotel,cruise,tour,transfer,rail,insurance,dining,car,event`. A component can't move to another booking. Reorder takes the full top-level order. Field formats: `booking-components.md`. |
| `booking_component_delete` 🗑️ | `id`, `ifMatch` | Confirm; call `booking_component_view` first for the etag. |
| `booking_financial_save` ✍️⚠️ | `request` is **`add_payment_to_supplier`** `{bookingId,ifMatch,payment:{amount:{amount,currency},dueDate,paymentMethod,subject,paidDate?,isPaidAtCheckout?,notes?,id?,paymentId?}}`, **`update_payment_to_supplier`** `{bookingId,ifMatch,paymentToSupplierId,changes}`, or **`update_refund`** `{bookingId,ifMatch,refundId,changes}` | Money OUT. Call `booking_payment_to_supplier_method_list` first. Omit `paidDate` for a pending schedule entry; include it to record that the supplier was paid; `paidDate:null` on update reverts to pending and voids the paid record. On AGENCY-paid bookings the schedule must total the fare. ARC refunds can't be changed here. |
| `booking_payment_to_supplier_delete` 🗑️ | `id` (booking), `paymentToSupplierId`, `ifMatch` | Voids any paid record for it too. Can't remove a payment already sent for payout. Confirm. |
| `booking_refund_create` ⚠️ | `id` (booking), `ifMatch`, `body:{amount:{amount,currency}, baseFareAmount?, estimatedCommissionAmount?, penalty?, commissionPenalty?, paymentMethod?, refundedAt?, lastFour?, cardCode?}` | Reversal of booking value (supplier-side), not a client-payment refund. Normally can't exceed remaining refundable amount. ARC bookings excluded. |
| `booking_cancel` ⚠️ | `id`, `ifMatch`, optional `expand`,`fields` | Does **not** void payments or clear commission. If it's the trip's last active booking, the trip is cancelled too. Not for voided bookings or locked trips. |
| `booking_void_or_delete` ⚠️🗑️ | `action:"void"\|"delete"`, `id`, `ifMatch` | `void`: clears sale amounts and voids active expense payments (not for ARC; not if commissions were paid). `delete`: hides booking + its refunds/expenses/payments (blocked by protected supplier payouts or locked ARC weeks). |
| `booking_supplier_invoice_download` 🔎 | `id` | PDF of the **commission invoice sent to the supplier** (money owed to the agency). Booking must be confirmed. Link expires ~1 hour; re-call for a fresh one. Not a client bill. |

## 6. Suppliers

| Tool | Purpose / key args | Notes |
|---|---|---|
| `supplier_search` 🔎 | `id`, `name` (**exact**, case-insensitive: the duplicate check), `q` (ranked, typo-tolerant, ≥2 chars; 2-char terms match Sabre vendor codes like `WN`), `queryOn`, `interfaceId`, `type_in` (`HOTEL,CRUISE_LINE,…`), `parentId`, `isParent`, `isRetired`, `fields` | `fields=defaultCommissionPercent,defaultCommissionDueDateOffset,defaultCommissionDueDateReference` for booking commission defaults. Only the org's own suppliers are listed; a booking may reference a **shared** supplier (`isShared:true`): fetch the booking's `supplierId` by exact id. Shared suppliers can't be updated. |
| `supplier_create` ✍️ | `body:{name,type,…}` | Search by exact `name` first; create only if empty. `type` ∈ AIRLINE, CRUISE_LINE, HOTEL, INSURANCE, RAIL, TOUR_DMC, TRANSPORTATION, ANCILLARIES, OTHER. `interfaceId` is a Sabre GDS id: never store your own partner ids there. |
| `supplier_update` ✍️ | `id`, `ifMatch`, `body` | Lists (`tags`, `badgeIds`, `destinationIds`, `associatedSupplierIds`) replace in full. `badgeIds` aren't discoverable here. |

## 7. Client payments (money IN from clients)

An amount the **agency** bills or collects: either separate **FEES** (service fees) or **TRIP** costs when the agency is the payer to suppliers. See `money-flows.md`.

| Tool | Purpose / key args | Notes |
|---|---|---|
| `client_payment_search` 🔎 | `id`, `q` (≥3 chars), `clientId`, `tripId`, `invoiceFor` (`FEES`\|`TRIP`), `status_in` (`active,paid,canceled,voided`), `dueDate_*`, `expand=client,trip,payments,udids`, `fields` (incl. `totalCharged`, `isVoidable`, `isDeletable`, `supportsDirectPayment`, `undeletableReasons`) | Check `isVoidable`/`isDeletable` before offering those actions. |
| `client_payment_save` ✍️⚠️ | `request` is **`create`** `{payment:{id,tripId,clientId,subject,invoiceFor,total:{amount,currency},dueDate,feeTypeId?,paymentMethods?,clientPaysProcessingCosts?,processingCostPct?,notes?}}` or **`update`** `{clientPaymentId,ifMatch,changes}` | Unpaid payments need `dueDate`. FEES need `feeTypeId`. Currency = org home unless user names another (must be in `clientPaymentCurrencies`). Omit `processingCostPct` for TripSuite CC/ACH processing. **Never compute `totalCharged`**: read it from the response. Processed payments have locked financial fields. |
| `client_payment_mark_paid` ⚠️ | `id`, `ifMatch`, `body:{clientPaymentMethodId, paidAt}` | Records money received **outside** TripSuite via a saved method with `supportsDirectPayment:false`. Never use for TripSuite CC/ACH Processing (needs the real processor flow). |
| `client_payment_refund` ⚠️ | `id`, `ifMatch`, `body:{refundedAmount, refundPaymentMethod?, refundIssuedAt?, refundedProcessingCostAmount?, source?}` | Only on **paid** payments. Card refunds are recorded as *pending*; the processor reversal is **not** performed automatically. Tell the user. |
| `client_payment_void_or_delete` ⚠️🗑️ | `action:"void"\|"delete"`, `id`, `ifMatch` | `delete` hides it and updates advisor payouts (processed payments, locked ARC weeks, and some >24h-old payments can't be removed). `void` clears the amount (not for TripSuite-processed or ARC). |

## 8. Trip invoices (client-facing documents)

A Trip Invoice is the **document** the client sees on the trip's Invoices tab. It is *not* a payment record. Its line items point at bookings (to authorize supplier charges) or client payments (to collect).

| Tool | Purpose / key args | Notes |
|---|---|---|
| `trip_invoice_search` 🔎 | `id`, `tripId`, `clientId`, `q`, `updatedAt_*`, `sort` (cursor supports `-createdAt`,`-updatedAt` only) | Exact fetch returns `data.lineItems[].id` and `…subItems[].id` + `etag`. |
| `trip_invoice_save` ✍️ | `request` is **`create`** `{invoice:{tripId,clientId,currency,dueDate,clientPaysProcessingCosts,paymentMethodIds[],lineItems[],memo?,terms?,showComponents?,requireThreeDs?}}` or **`update`** `{invoiceId,ifMatch,changes}` | Each line item `{order, bookingId? \| clientPaymentId?, id, subItems:[{order, clientAction, bookingExpenseId?, id}]}`. `clientAction` ∈ `REQUEST_PAYMENT`, `REQUEST_AUTHORIZATION`, `DOCUMENT_ONLY`. On update, `lineItems` and `paymentMethodIds` **replace** the lists. `memo`/`terms` are printed to the client: polished and non-internal only. |
| `trip_invoice_duplicate` ✍️ | `id`, `ifMatch` | Copies the document and active details on the same trip. Does not duplicate payments. Drops `requireThreeDs`. |
| `trip_invoice_delete` 🗑️ | `id`, `ifMatch` | Only unpaid, unauthorized invoices. Confirm. |

## 9. Commissions (money IN from suppliers)

| Tool | Purpose / key args | Notes |
|---|---|---|
| `commission_search` 🔎 | `id`, `bookingId`, `status_in` (`active,voided`), `reconciledAt_*`, `createdAt_*`, `expand=group,booking`, `fields` (`amountUsd,amountHome,receivedDate,reconciledAt,supplierNameActual,…`) | Read-only. Expected commission lives on the booking (`estimatedCommission`, `commissionDueDate`, `commissionStatus`, `supplierCommissionState`, `commissionPaidAt` via `booking_search fields=`). `commissionGroupId` can only be used if the user supplies it. |

## 10. Tasks

| Tool | Purpose / key args | Notes |
|---|---|---|
| `task_search` 🔎 | `id`, `tripId`, `clientId`, `assignedAdvisorId`, `isCompleted`, `dueAt_gte/_lt`, `remindAt_*`, `isDateReminder`, `type` (`BIRTHDAY`,`ANNIVERSARY`,`PASSPORT_EXPIRATION`), `expand=trip,client,assignedAdvisors`, `sort=dueAt` | Default excludes date reminders: they're never overdue. |
| `task_save` ✍️ | `request` is **`create`** `{task:{title,description,dueAt,remindAt,tripId,clientId,assignedAdvisorIds[]}}` or **`update`** `{taskId,changes:{title,description,dueAt,remindAt,isCompleted,assignedAdvisorIds}}` | **No `ifMatch`.** Must link to at least one trip or client. Defaults to the current advisor under user access; organization access must provide an advisor from `user_search`. If `dueAt` omitted but `remindAt` given, the reminder is also the due date. Linked trip/client/type can't change. |
| `task_delete` 🗑️ | Removes a task (after the user confirms). | Schema wasn't captured when this catalog was written. Load it via tool search before calling and use the exact parameter names it returns (expect the task id). |

## 11. Attachments

| Tool | Purpose / key args | Notes |
|---|---|---|
| `attachment_create` ✍️ | `body:{entityType, entityId, name, contentBase64+contentType \| externalFilename}` | `entityType` ∈ `trip`, `booking`, `client`, `supplier`, `booking_expense`; `entityId` must match the type (booking_expense id = `booking_search data.expenses[].id`). `name` includes extension. Exactly one of `contentBase64` (≤256 KB decoded; bytes pass through the model) or `externalFilename`. The returned attachment `id` feeds `booking_source_extract.attachmentIds`. |
| `attachment_upload_url_create` ✍️ | `body:{filename, contentType}` | Returns `writeUrl` + `externalFilename`. You must HTTP `PUT` the bytes to `writeUrl` with the **same** `Content-Type`, then call `attachment_create` with `externalFilename`. Nothing is attached until you do. Only use if you can actually perform the PUT; otherwise use inline for small files or tell the user to upload in the app. |

## 12. Statements (advisor/agency payouts)

Statements are bucketed into **periods**. Payouts are **not prorated** to partial dates, so always work in whole periods.

| Tool | Purpose / key args | Notes |
|---|---|---|
| `statement_summary_list` 🔎 | `startDate`, `endDate` (YYYY-MM-DD), paging | Returns period buckets. For a quarter/range, collect **all pages**, then query each returned `startDate`. Report actual period bounds if they extend beyond the request. |
| `statement_recipient_search` 🔎 | `startDate` (any date in the period), `agencyId?`, `type?` (`bookings`\|`trips`\|`expenses`), `query?`, `sort` (`recipient`\|`payout`) | Returns `data[].recipient.user.id` (advisor) and `.recipient.agency.id`. Omit `type` for aggregates. Visibility depends on role. |
| `statement_user_view` 🔎 | `userId`, `startDate`, `type?`, paging, `sort` (many columns) | Own statement: `userId = user_current_view.currentUserId` (no search needed). |
| `statement_agency_recipient_list` 🔎 | `agencyId` (or `"inactive"` only when explicitly asked), `startDate` | Agencies/advisors paid by an agency in a period. |

## 13. Feedback

| Tool | Purpose / key args | Notes |
|---|---|---|
| `feedback_submit` ✍️ | `category` (`confusing_instructions`,`missing_capability`,`unexpected_result`,`invalid_input_guidance`,`reliability`,`other`), `summary`, `affectedTool?`, `expectedBehavior?`, `actualBehavior?`, `suggestion?` | Use proactively when the MCP slows you down. **No secrets or customer personal data.** Describe the shape of the problem, not the record. |
