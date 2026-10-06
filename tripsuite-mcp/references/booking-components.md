# Booking components and field formats

Components are the itinerary pieces inside a booking. They are created together with the booking (`booking_save create_booking` → `booking.components[]`) and edited later with `booking_component_save`.

## Contents
1. [Format cheat-sheet](#1-format-cheat-sheet)
2. [Common fields on every component](#2-common-fields-on-every-component)
3. [Per-type fields](#3-per-type-fields)
4. [Rules for building components from a source document](#4-rules-for-building-components-from-a-source-document)
5. [Booking-level fields](#5-booking-level-fields)

---

## 1. Format cheat-sheet

Formats differ by field. The server rejects the wrong one. `scripts/lint_payload.py` checks these.

| Kind | Format | Example | Where |
|---|---|---|---|
| Civil date | `YYYY-MM-DD` | `2027-11-07` | trip/booking/component `startDate`/`endDate`, `bookedDate`, `commissionDueDate`, `paidDate`, invoice/payment `dueDate` (client payments, trip invoices, `add_payment_to_supplier`), profile dates |
| Time of day | `HH:MM` 24-hour | `14:30` | component `startTime`/`endTime`, transfer `departTime`/`arrivalTime` |
| Local wall-time datetime | `YYYY-MM-DDTHH:mm:ss` **no offset** | `2026-08-03T14:30:00` | air/rail segment `scheduledDeparture/Arrival`, `actualDeparture/Arrival` |
| UTC datetime | ends in `Z` | `2026-08-03T21:30:00.000Z` | alternative for segments; **required** for car `pickupDateTime`/`returnDateTime` |
| Datetime with timezone | ISO 8601 with `Z` or offset | `2026-08-03T14:30:00.000-07:00` | `booking_save` `expenses[].dueDate`, `exchangeRateLockedAt` |
| Datetime with offset | ISO 8601 | `2026-11-01T00:00:00Z` | search filters (`startDate_gte`…), task `dueAt`/`remindAt`, `paidAt` on mark-paid, `refundedAt` |
| Strict UTC millis | `YYYY-MM-DDTHH:mm:ss.sssZ` | `2026-10-04T00:00:00.000Z` | `trip_cancel` refund `refundedAt`/`exchangeRateLockedAt` |
| Money | decimal string + ISO currency | `{"amount":"266.00","currency":"USD"}` | all amounts |
| Percent | number | `10` | `commissionPercent`, `processingCostPct`, `takePercent` |

**Note the supplier-payment date inconsistency:** `booking_save` `expenses[].dueDate` is an ISO **datetime with timezone**, whereas `booking_financial_save add_payment_to_supplier` `payment.dueDate` is a civil **`YYYY-MM-DD`**.

Segment times: **numeric offsets (`-07:00`) are rejected** on air/rail segments. Use local wall time (no offset) or `Z`.

## 2. Common fields on every component

| Field | Notes |
|---|---|
| `type` | **Required.** `air`, `hotel`, `cruise`, `tour`, `transfer`, `rail`, `insurance`, `dining`, `car`, `event` |
| `title`, `description` | Free text (nullable) |
| `startDate`, `endDate`, `startTime`, `endTime` | Formats above |
| `sortOrder` | Integer ≥0; preserve the document's order |
| `parentComponentId` | Nest a component under another (id from `booking_search … expand=components`); omit for top-level |
| `serviceProviderSupplierId` | Preferred: supplier id from `supplier_search` |
| `serviceProviderName` | Free-text provider name when there's no supplier record |
| `serviceProviderId` | Not discoverable here; only if the user supplied it |
| `id` | Only when changing an existing component inside a booking-level payload; omit for new |
| Type-specific object | Key matches the type: `air`, `hotel`, `cruise`, `tour`, `transfer`, `rail`, `insurance`, `dining`, `car` (`event` has none) |

All type-specific objects also accept `extendedDetails` (free-form object) for supplier-specific extras.

## 3. Per-type fields

**air** (`air:{…}`)
- `recordLocator`, `ticketNumber`, `ticketingAirlineCode` (≤3), `displayAs` (`summary|segments|legs`)
- `segments[]` (each needs `segmentOrder` ≥0): `flightNumber`, `operatingCarrier`, `operatingFlightNumber`, `departureAirport`/`arrivalAirport` (IATA, ≤4 chars), `departureCity/Country/AirportName/Terminal/Gate` (and arrival equivalents), `scheduledDeparture/Arrival`, `actualDeparture/Arrival`, `durationMinutes`, `aircraftType/aircraftCode`, `cabinClass`, `bookingClass` (≤2), `seat`, `seatTicketDetails`, `status` (`scheduled|delayed|cancelled|completed`), `segmentName`. Include `id` only to edit an existing segment.

**hotel** (`hotel:{…}`): `confirmationNumber`, `roomCategory`, `address`, `amenities`. Hotel perks (including Virtuoso amenities) go in `amenities` on the hotel component. **Never** invent a separate component for them. `startDate`/`endDate` = check-in/out.

**cruise** (`cruise:{…}`): `shipName`, `sailingName`, `voyageId` (from the supplier/source; external), `cabinNumber`, `cabinCategory`, `cabinClass`, `embarkationPort`, `disembarkationPort`.

**tour** (`tour:{…}`): `duration`, `startLocation`, `endLocation`, `pickupLocation`, `contactName`, `contactPhone`.

**transfer** (`transfer:{…}`): `startLocation`, `endLocation`, `departTime`, `arrivalTime` (HH:MM), `confirmationNumber`, `contactName`, `contactPhone`.

**rail** (`rail:{…}`): `trainNumber`, `segments[]` (`segmentOrder`, `departureStation/City/Location`, `arrivalStation/City/Location`, `scheduledDeparture/Arrival`, `durationMinutes`, `segmentName`).

**insurance** (`insurance:{…}`): `policyName`.

**dining** (`dining:{…}`): `venueName`, `address`.

**car** (`car:{…}`): `vendorCode`, `confirmationNumber`, `vehicleClass`, `vehicleDescription`, `mileageAllowance`, `pickupLocation`, `returnLocation`, `pickupDateTime`/`returnDateTime` (**UTC `Z` only**).

**event**: common fields only.

## 4. Rules for building components from a source document

1. **Run `booking_source_extract` first** and read its coverage inventory and issues before building. Preserve the proposed field values and order.
2. **Include every identifiable supported component**; **never invent placeholders.** If the source has no identifiable component, omit `components` or send `[]`.
3. **Grouped visits:** split them (e.g. a "3 nights Paris + 2 nights Lyon" package is two hotel components).
4. **Optional/alternative arrangements** are not confirmed; don't add them as confirmed components. Surface them to the user.
5. **Confirmation numbers:** put the hotel/transfer/car confirmation on the component where the type has a field; the *booking's* `confirmationNumber` is the supplier confirmation for the reservation. Don't fabricate either.
6. **Times:** keep source local times. Don't convert time zones; don't add offsets to segment times.
7. **Ordering:** `sortOrder` follows the document order (0-based). Use `reorder_components` later if needed.
8. **One reservation = one booking.** Don't create one booking per component of the same supplier reservation.

## 5. Booking-level fields

Required on create: `tripId`, `supplierId`, `startDate` (check-in), `endDate` (check-out), `totalAmount {amount,currency}`, `payingEntity`, `isCommissionable`.

Common optional: `id` (UUIDv4), `confirmationNumber` (required when confirmed), `isConfirmed` (default true), `bookedDate`, `clientId` (defaults to trip primary), `corporateGroupId`, `currency`, `baseFare`, `taxesAndFees`, `originalTotalAmount`, `penalty`, `estimatedCommission`, `commissionPercent`, `commissionDueDate`, `bookingType` (`Exchange|Fare_Difference|Credit_Debit_Memo|AIR_NDC`; omit for ordinary), `notes`, `exchangeRate` (omit unless user-supplied), `expenses[]`, `components[]`.

On update (`changes`): same fields plus `additionalClientIds[]` (replace), `splits[]` (replace), `udids[]` (replace), `dkNumberOverride`. `isCommissionable:false` zeroes the estimated commission and clears the commission due date. `supplierId` replacement must be an org supplier. Voided bookings and locked ARC financial details can't be changed.

Booking `startDate`/`endDate` are the **booking's** check-in/check-out, not the trip's. `booking_search endDate_*` filters check-out, not trip end.
