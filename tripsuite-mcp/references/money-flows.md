# Money flows in TripSuite

**Read this before any write that involves an amount.** TripSuite models money in four separate places. They look similar and the tool names overlap, so picking the wrong one silently double-books revenue, bills clients for the wrong thing, or leaves supplier schedules inconsistent.

## Contents
1. [The four concepts](#1-the-four-concepts)
2. [The single most important question: who pays the supplier?](#2-the-single-most-important-question-who-pays-the-supplier)
3. [Decision table: what the user said → what to use](#3-decision-table)
4. [Trip invoices in detail](#4-trip-invoices-in-detail)
5. [Refunds: three different things](#5-refunds-three-different-things)
6. [Cancel vs void vs delete vs inactive](#6-cancel-vs-void-vs-delete-vs-inactive)
7. [Commission](#7-commission)
8. [Currency, processing costs, exchange rates](#8-currency-processing-costs-exchange-rates)
9. [Three different "payment method" lists](#9-three-different-payment-method-lists)
10. [Worked examples](#10-worked-examples)

---

## 1. The four concepts

| Concept | Direction | Meaning | Lives on | Tools |
|---|---|---|---|---|
| **Client payment** | money **IN** from client → agency | What the *agency* bills/collects: separate **FEES** (planning/service fees) or **TRIP** costs when the agency is the payer to suppliers | Trip + client | `client_payment_search`, `client_payment_save`, `client_payment_mark_paid`, `client_payment_refund`, `client_payment_void_or_delete`, `client_payment_configuration_view` |
| **Trip invoice** | *document* | The client-facing invoice/authorization page on the trip's **Invoices tab**. Moves no money by itself. Its items point at bookings/expenses (to authorize) or client payments (to collect). | Trip | `trip_invoice_search`, `trip_invoice_save`, `trip_invoice_duplicate`, `trip_invoice_delete`, `trip_invoice_payment_method_list` |
| **Payment to supplier** ("expense") | money **OUT** → supplier | Deposits, installments, finals owed or paid to the supplier for a booking | Booking (`expenses`) | `booking_save` (initial), `booking_financial_save`, `booking_payment_to_supplier_delete`, `booking_payment_to_supplier_method_list` |
| **Commission** | money **IN** from supplier → agency | Commission expected/received on a booking | Booking (fields) + commission records | `commission_search` (read-only), booking fields via `booking_search`, `booking_supplier_invoice_download` |

Never use one to represent another: a client payment is **not** a trip invoice; a supplier deposit on a client-paid booking is **not** a client payment; a commission receipt is not a payment to a supplier.

## 2. The single most important question: who pays the supplier?

Every booking has `payingEntity`:

### `CLIENT`: the client pays the supplier directly
- The advisor normally submits the supplier charge using the **client's** payment method. The booking still carries its payment-to-supplier schedule (deposit/final) so the charge is tracked and can be authorized.
- **Do not create `TRIP` client payments for this booking's supplier costs.** The agency isn't collecting that money.
- To get the client's approval of an advisor-submitted charge: Trip Invoice with `REQUEST_AUTHORIZATION` on the booking's items (no payment methods; `paymentMethodIds: []`).
- Separate agency service fees can still be billed to the client with a `FEES` client payment (+ invoice `REQUEST_PAYMENT`).
- TripSuite-funded supplier methods (`TS_BANK_TRANSFER`, `TS_VIRTUAL_CARD`) are **rejected** on CLIENT-paying bookings (409 `CLIENT_PAID_TS_PAYMENT_UNSUPPORTED`).

### `AGENCY`: the agency pays the supplier from agency funds
- The agency owes the supplier the fare, so **`booking_save create_booking` requires `expenses[]`** whose amounts sum to the booking fare in the booking currency (else 422). Ask the user for the schedule (deposit/final or single payment, method, due dates, whether any is already paid). Do not invent it.
- The agency collects from the client with `TRIP` client payments (often installments), billed via a Trip Invoice with `REQUEST_PAYMENT` on those client payments.
- Re-pricing (changing total or currency) or converting to agency-paid while existing supplier payments disagree is rejected (`AGENCY_SCHEDULE_MISMATCH`). **Fix the supplier payments first** with `booking_financial_save update_payment_to_supplier` / `add_payment_to_supplier`, then re-send the booking change. Never "solve" it by flipping to client-paid.

**Never assume the paying entity.** Take it from the source document or ask: "Is the client paying the supplier directly, or is the agency paying and collecting from the client?"

## 3. Decision table

| User says… | Do this |
|---|---|
| "Charge her a $250 planning fee" | `client_payment_configuration_view fee_types` → `client_payment_save create` `invoiceFor:"FEES"` with `feeTypeId`, `dueDate`; optionally invoice it (`REQUEST_PAYMENT`) |
| "Bill the client for the hotel; we're paying the hotel" | Booking is AGENCY-paid → `client_payment_save create` `invoiceFor:"TRIP"` → invoice `REQUEST_PAYMENT` |
| "Hotel is client-paid; get her to approve the deposit" | Invoice with `REQUEST_AUTHORIZATION` on booking + `bookingExpenseId` sub-items; `paymentMethodIds: []`. **No** client payment. |
| "Record the $1,000 hotel deposit due Friday" | `booking_payment_to_supplier_method_list` → `booking_financial_save add_payment_to_supplier` (pending: omit `paidDate`) |
| "We paid the hotel deposit today by Amex" | Same, with `paidDate` (and `paymentMethod: CREDIT_CARD`) |
| "Client mailed a check for the fee" | `saved_payment_methods` → pick the method with `supportsDirectPayment:false` → `client_payment_mark_paid` (`paidAt`) |
| "Client paid by card through TripSuite" | Not manual; that flow happens through the payment page. Don't mark paid. |
| "Issue a receipt showing what's been paid" | Invoice with `DOCUMENT_ONLY` items; `paymentMethodIds: []` |
| "Send the supplier our commission invoice" | `booking_supplier_invoice_download` (booking must be confirmed) |
| "What commission is outstanding?" | `booking_search fields=…commission…` and `commission_search` |

## 4. Trip invoices in detail

Structure:

```
invoice (tripId, clientId, currency, dueDate, clientPaysProcessingCosts, paymentMethodIds[], memo?, terms?, showComponents?, requireThreeDs?)
 └─ lineItems[] { id, order, bookingId?  XOR  clientPaymentId? }
     └─ subItems[] { id, order, clientAction, bookingExpenseId? }
```

`clientAction`:
| Value | Meaning | Pair with | Collects money? |
|---|---|---|---|
| `REQUEST_PAYMENT` | Client pays the **agency** | `clientPaymentId` on the line item | Yes (needs `paymentMethodIds`) |
| `REQUEST_AUTHORIZATION` | Client approves an advisor-submitted **supplier** charge | `bookingId` on the line item + `bookingExpenseId` on the sub-item | No |
| `DOCUMENT_ONLY` | Shows an amount already handled | either | No |

Rules:
- Mixed invoices (authorization + payment) are allowed; TripSuite derives payment-page behavior.
- If **any** item is `REQUEST_PAYMENT`: call `trip_invoice_payment_method_list`, include **all** returned IDs by default (unless the advisor asks for a subset), and tell the advisor which methods were enabled so they can narrow it. The request is rejected without at least one eligible method.
- If there is **no** `REQUEST_PAYMENT`: `paymentMethodIds: []`, and don't talk about collection methods.
- Currency: org home unless the user asks otherwise.
- `memo` and `terms` are **client-facing**: concise, polished; never internal reasoning, estimates, pending confirmations, payment-routing commentary, or sensitive profile data.
- `requireThreeDs` only if 3-D Secure is enabled for the org (otherwise rejected). Duplicating drops it.
- On update, `lineItems` and `paymentMethodIds` **replace** the full lists: fetch current, modify, send complete.
- Only unpaid, unauthorized invoices can be deleted.
- Create the underlying client payment(s) **first**, then the invoice that references them.

## 5. Refunds: three different things

| Situation | Tool | Notes |
|---|---|---|
| Supplier-side reversal: the booking's value goes down (supplier refunds / penalty) | `booking_refund_create` (change later with `booking_financial_save update_refund`) | Recalculates booking totals. Amount can't normally exceed remaining refundable. Include `baseFareAmount`, `estimatedCommissionAmount`, `penalty`, `commissionPenalty` when known: they adjust base fare/commission. **Not for ARC bookings.** |
| Returning money to the **client** for a paid client payment | `client_payment_refund` | Only on **paid** payments. Card refunds are recorded *pending*: the processor reversal is **not** done automatically. Say so. |
| Whole-trip cancellation with refunds | `trip_cancel` with `cancellation.tripItemRefunds` | Entries: `{type:"BOOKING", itemId:<booking id>, amount,…}` and `{type:"CLIENT_INVOICE", itemId:<client payment id>, amount,…}`. Dates must be `YYYY-MM-DDTHH:mm:ss.sssZ`. |

## 6. Cancel vs void vs delete vs inactive

| Verb | What it does | Reversible? | Notes |
|---|---|---|---|
| **Cancel** booking (`booking_cancel`) | Marks it cancelled. **Does not** void payments or clear commission. If last active booking → trip also cancels. | Trip can be reinstated, but bookings/payments stay cancelled | Not for voided bookings / locked trips |
| **Cancel** trip (`trip_cancel`) | Cancels trip + **all active bookings + all active client payments**, optionally records refunds | `reinstate` restores **only** the trip status | Locked trips excluded |
| **Void** (`booking_void_or_delete` / `client_payment_void_or_delete` with `action:"void"`) | Clears sale amounts / amount and voids related payments: the financial record is wiped | Treat as not reversible | Not for ARC; booking not if commissions were **paid**; not for TripSuite-processed client payments |
| **Delete** (`*_delete`) | Hides the record (and for bookings: refunds/expenses/payments) from searches | Yes (hide-only, per tool docs) | Blocked by protected supplier payouts, locked ARC weeks, processed payments, some >24h-old payments |
| **Inactive** (`client_status_set`) | Keeps profile/history, flags inactive | Yes | Prefer for clients with history |

Check `isVoidable`, `isDeletable`, `unvoidableReasons`, `undeletableReasons` (via `fields=`) before offering void/delete.

## 7. Commission

- Booking fields: `isCommissionable`, `estimatedCommission`, `commissionPercent`, `baseFare`, `commissionDueDate`, plus read-only `commissionStatus`, `supplierCommissionState`, `commissionPaidAt`.
- **`isCommissionable: true` requires a positive `estimatedCommission` or `commissionPercent`.** If both are given they must agree.
- **Don't infer commissionability** from silence or from a supplier default. If the source doesn't say, ask. Use `false` only when the source or the user explicitly says non-commissionable (then no commission amount and no due date).
- If the source **explicitly says commissionable** but omits amount and percent: `supplier_search id=<supplier> fields=defaultCommissionPercent,defaultCommissionDueDateOffset,defaultCommissionDueDateReference`. Use a **positive** `defaultCommissionPercent` as `commissionPercent`; if none, ask the user.
- If the due date is missing and both default due-date fields exist, compute `commissionDueDate`:
  - `BEFORE_CHECK_IN`: check-in (`startDate`) minus offset days
  - `AFTER_CHECK_OUT`: check-out (`endDate`) plus offset days
  - `AFTER_BOOKED_DATE`: `bookedDate` plus offset days
- Always preserve explicit amounts/percents/dates from the source.
- `commission_search` is read-only (amounts in `amountUsd`/`amountHome`, `receivedDate`, `reconciledAt`). TripSuite doesn't let you create/reconcile commission records through this MCP.
- Commission **splits** between advisors/agencies are set on the booking (`update_booking changes.splits[]`: `{advisorId, agencyId?, takePercent}`); replace-style list.

## 8. Currency, processing costs, exchange rates

- **Home currency & accepted client-payment currencies:** `organization_view fields=homeCurrency,clientPaymentCurrencies`. Default to home currency for client payments and trip invoices; use another only if the user explicitly names it **and** it's in `clientPaymentCurrencies`.
- **Booking currency** is whatever the supplier priced in (`totalAmount.currency`). Supplier payments carry their own currency.
- **Exchange rates:** never estimate or web-search one, never ask the user for one just because the field is blank. Omit `exchangeRate` and TripSuite applies its canonical daily rate. Only send `exchangeRate` if the user explicitly supplies or chooses a manual rate, and send it unchanged.
- **Processing costs on client payments:**
  - `clientPaysProcessingCosts: true` only if the user asked to pass costs to the client; otherwise omit (agency absorbs).
  - Send `processingCostPct` only if the user stated a rate; **omit it for TripSuite CC/ACH Processing** (the real processor path applies the org's rate).
  - **Never calculate the amount charged yourself.** Read `totalCharged` (and `processingCost`) from the API response.
- **Formats:** amounts are decimal **strings** in major units (`"266.00"`), objects `{amount, currency}`. Percents/rates are numbers.

## 9. Three different "payment method" lists

Don't mix these up. Each tool uses a different vocabulary:

| Context | Source | Values | Used in |
|---|---|---|---|
| Money **OUT** to suppliers | `booking_payment_to_supplier_method_list` (what the org permits) | enum: `CREDIT_CARD, ACH, CHECK, WIRE, CASH, GIFT_CARD, TS_BANK_TRANSFER, TS_VIRTUAL_CARD` | `paymentMethod` on supplier payments, refunds |
| Money **IN**, manual receipt | `client_payment_configuration_view {saved_payment_methods}` | UUIDs; use only where `supportsDirectPayment:false` | `client_payment_mark_paid.clientPaymentMethodId` |
| Money **IN**, invoice payment page | `trip_invoice_payment_method_list` | UUIDs | `trip_invoice_save paymentMethodIds` |
| Label on a client payment | n/a | `CREDIT_CARD, ACH, CHECK, WIRE, CASH, GIFT_CARD` | `client_payment_save paymentMethods` (labels only, not IDs) |

TripSuite-funded supplier methods (`TS_BANK_TRANSFER`, `TS_VIRTUAL_CARD`): AGENCY-paid bookings only, and only if the org is entitled (else 403 `PAYMENT_METHOD_NOT_ENTITLED`); offer only what the method list returns.

## 10. Worked examples

**A. Client-paid hotel with a deposit the client must approve, plus a $200 fee**
1. `booking_save create_booking` with `payingEntity:"CLIENT"` (+ confirmation #, commission info, components). Add the deposit as `expenses[0]` (method `CREDIT_CARD`, due date, pending).
2. `client_payment_configuration_view fee_types` → `client_payment_save create` `{invoiceFor:"FEES", feeTypeId, total:{amount:"200.00", currency:<home>}, dueDate}`.
3. `trip_invoice_payment_method_list` → `trip_invoice_save create` with two line items: (a) `bookingId` + sub-item `{clientAction:"REQUEST_AUTHORIZATION", bookingExpenseId}`; (b) `clientPaymentId` + sub-item `{clientAction:"REQUEST_PAYMENT"}`; `paymentMethodIds` = all returned (because (b) collects money). Tell the advisor which methods were enabled.

**B. Agency-paid cruise, client pays in two installments**
1. `booking_save create_booking` `payingEntity:"AGENCY"`, `expenses` = deposit + final (sum = fare), methods from the permitted list.
2. Two `client_payment_save create` `{invoiceFor:"TRIP"}` (installment 1 and 2, due dates).
3. One invoice with both client payments as `REQUEST_PAYMENT` line items; all methods enabled.
4. As the client's money arrives outside TripSuite: `client_payment_mark_paid`. As the agency pays the cruise line: `booking_financial_save update_payment_to_supplier` with `paidDate`.

**C. Trip cancelled after deposit paid; supplier refunds $600, client refunded $500**
1. Fetch the trip (etag), list its bookings and client payments, summarize what cancels.
2. Ask: refund amounts, methods, dates. Get a yes.
3. `trip_cancel` `{operation:"cancel", tripId, ifMatch, cancellation:{tripItemRefunds:[{type:"BOOKING", itemId:<booking>, amount:"600.00", …},{type:"CLIENT_INVOICE", itemId:<clientPayment>, amount:"500.00", …}]}}`.
4. If the client's payment was a card, tell the user the processor reversal is not automatic.
