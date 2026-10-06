#!/usr/bin/env python3
"""
Lint a TripSuite MCP request payload for the mistakes that most often get rejected
or corrupt data. Offline; no network.

Usage:
  lint_payload.py payload.json          # file containing {"tool": "...", "arguments": {...}}
                                        # or just the arguments object (e.g. {"request": {...}})
  cat payload.json | lint_payload.py -

Exit code 0 = no errors (warnings allowed), 1 = errors found.
Placeholders like "<client id from client_search>" are ignored.
"""
import json, re, sys

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
UUID4_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
CIVIL = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HHMM = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
MONEY = re.compile(r"^-?\d+(\.\d+)?$")
ISO_TZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$")
LOCAL_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$")
UTC_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?Z$")
STRICT_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

CIVIL_KEYS = {"startDate", "endDate", "bookedDate", "commissionDueDate", "paidDate",
              "birthday", "anniversary", "expirationDate", "refundReceivedDate"}
TIME_KEYS = {"startTime", "endTime", "departTime", "arrivalTime"}
SEGMENT_DT_KEYS = {"scheduledDeparture", "scheduledArrival", "actualDeparture", "actualArrival"}
UTC_ONLY_KEYS = {"pickupDateTime", "returnDateTime"}
NON_UUID_ID_KEYS = {"voyageId", "externalClientId", "interfaceId", "externalFilename", "serviceProviderName"}
GENERATED_ID_PATHS = {"booking.id", "payment.id", "payment.paymentId", "lineItems.id", "subItems.id"}

errors, warnings = [], []


def is_placeholder(v):
    return isinstance(v, str) and v.strip().startswith("<")


def err(path, msg):
    errors.append(f"ERROR  {path}: {msg}")


def warn(path, msg):
    warnings.append(f"WARN   {path}: {msg}")


def walk(node, path="", parent_keys=()):
    if isinstance(node, dict):
        # money objects
        if "amount" in node and "currency" in node and set(node) <= {"amount", "currency"}:
            amt, cur = node["amount"], node["currency"]
            if not is_placeholder(amt) and not (isinstance(amt, str) and MONEY.match(amt)):
                err(f"{path}.amount", f"money must be a decimal STRING like \"266.00\" (got {amt!r})")
            if not is_placeholder(cur) and not (isinstance(cur, str) and re.fullmatch(r"[A-Z]{3}", cur)):
                err(f"{path}.currency", f"currency must be ISO 4217 uppercase (got {cur!r})")
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            check_field(k, v, p, parent_keys)
            walk(v, p, parent_keys + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]", parent_keys)


def check_field(k, v, p, parents):
    if v is None or is_placeholder(v):
        return
    if k in CIVIL_KEYS and isinstance(v, str) and not CIVIL.match(v):
        err(p, f"expected civil date YYYY-MM-DD (got {v!r})")
    if k == "dueDate" and isinstance(v, str) and not (CIVIL.match(v) or ISO_TZ.match(v)):
        err(p, f"dueDate must be YYYY-MM-DD, or ISO datetime with timezone for booking_save expenses (got {v!r})")
    if k == "dueDate" and isinstance(v, str) and "expenses" in parents and CIVIL.match(v):
        warn(p, "booking_save expenses[].dueDate should be an ISO datetime WITH timezone (e.g. 2026-08-03T00:00:00.000Z)")
    if k == "dueDate" and isinstance(v, str) and "payment" in parents and "expenses" not in parents and ISO_TZ.match(v):
        warn(p, "add_payment_to_supplier payment.dueDate is a civil date YYYY-MM-DD")
    if k in TIME_KEYS and isinstance(v, str) and not HHMM.match(v):
        err(p, f"expected 24h HH:MM (got {v!r})")
    if k in SEGMENT_DT_KEYS and isinstance(v, str):
        if not (LOCAL_DT.match(v) or UTC_DT.match(v)):
            err(p, f"segment time must be local wall time without offset or UTC ending in Z; numeric offsets are rejected (got {v!r})")
    if k in UTC_ONLY_KEYS and isinstance(v, str) and not UTC_DT.match(v):
        err(p, f"car pickup/return must be UTC ending in Z (got {v!r})")
    if k in {"refundedAt", "exchangeRateLockedAt"} and "tripItemRefunds" in parents and isinstance(v, str) and not STRICT_UTC.match(v):
        err(p, f"trip_cancel refund timestamps must be YYYY-MM-DDTHH:mm:ss.sssZ (got {v!r})")
    if k in {"paidAt", "dueAt", "remindAt"} and isinstance(v, str) and not ISO_TZ.match(v):
        err(p, f"expected ISO 8601 datetime with timezone/offset (got {v!r})")
    if k in {"processingCostPct", "commissionPercent", "takePercent", "exchangeRate"} and isinstance(v, str):
        err(p, f"{k} must be a number, not a string")
    # IDs
    if (k.endswith("Id") or k == "id") and k not in NON_UUID_ID_KEYS and isinstance(v, str):
        if not UUID_RE.match(v):
            err(p, f"expected a UUID (got {v!r}); public IDs are only valid in search calls")
    if k.endswith("Ids") and k not in {"destinationIds"} and isinstance(v, list):
        for i, x in enumerate(v):
            if isinstance(x, str) and not is_placeholder(x) and not UUID_RE.match(x):
                err(f"{p}[{i}]", f"expected a UUID (got {x!r})")
    if k == "destinationIds" and isinstance(v, list):
        for i, x in enumerate(v):
            if not isinstance(x, (int, float)) or isinstance(x, bool):
                err(f"{p}[{i}]", "destination ids are numbers from destination_search")
    if k in {"id", "paymentId"} and isinstance(v, str) and UUID_RE.match(v) and not UUID4_RE.match(v):
        warn(p, "generated ids should be UUIDv4")
    if k == "ifMatch" and isinstance(v, str) and not v.strip():
        err(p, "ifMatch is empty; copy the top-level etag from a fresh exact-id fetch")


def find_requests(args):
    """Return list of (name, dict) operation bodies to check semantically."""
    out = []
    req = args.get("request") if isinstance(args, dict) else None
    if isinstance(req, dict):
        out.append(req)
    elif isinstance(args, dict):
        out.append(args)
    return out


def semantic(req):
    op = req.get("operation")
    if op in {"update", "update_trip", "update_booking", "update_client", "update_component", "update_payment_to_supplier",
              "update_refund", "set_stage", "cancel", "reinstate"} and "ifMatch" not in req:
        err("ifMatch", f"operation {op!r} normally requires ifMatch (etag from a fresh exact-id fetch)")

    if op == "create_trip":
        t = req.get("trip", {})
        for f in ("name", "travelType", "destinationIds"):
            if f not in t or t[f] in (None, "", []):
                err(f"trip.{f}", "required")
        if t.get("travelType") == "leisure" and "primaryClientId" not in t:
            err("trip.primaryClientId", "required for leisure trips")
        if t.get("travelType") == "corporate" and "corporateClientId" not in t:
            err("trip.corporateClientId", "required for corporate trips")
        if t.get("type") not in (None, "standard"):
            err("trip.type", "leave as 'standard'")

    if op == "create_booking":
        b = req.get("booking", {})
        for f in ("tripId", "supplierId", "startDate", "endDate", "totalAmount", "payingEntity", "isCommissionable"):
            if f not in b:
                err(f"booking.{f}", "required (ask the user for payingEntity / isCommissionable, never assume)")
        if "id" not in b:
            warn("booking.id", "generate a UUIDv4 for idempotent creation")
        if b.get("isConfirmed", True) and not b.get("confirmationNumber"):
            err("booking.confirmationNumber", "confirmed bookings need a supplier confirmation number (never invent one); set isConfirmed:false only if the source says proposed/quote/hold")
        if b.get("isCommissionable") is True and not (b.get("estimatedCommission") or b.get("commissionPercent")):
            err("booking", "isCommissionable:true needs a positive estimatedCommission or commissionPercent")
        if b.get("isCommissionable") is False and (b.get("estimatedCommission") not in (None, "0", "0.00") or b.get("commissionDueDate")):
            warn("booking", "non-commissionable booking should not carry commission amount/due date")
        if "exchangeRate" in b:
            warn("booking.exchangeRate", "omit unless the user explicitly supplied a manual rate")
        exp = b.get("expenses", [])
        if b.get("payingEntity") == "AGENCY":
            if not exp:
                err("booking.expenses", "AGENCY-paid bookings require payments to supplier that total the fare")
            else:
                try:
                    tot = b["totalAmount"]
                    if all(e["amount"]["currency"] == tot["currency"] for e in exp):
                        s = sum(float(e["amount"]["amount"]) for e in exp)
                        if abs(s - float(tot["amount"])) > 0.005:
                            err("booking.expenses", f"expenses sum {s:.2f} != totalAmount {tot['amount']}")
                except (KeyError, ValueError, TypeError):
                    pass
        for i, c in enumerate(b.get("components", [])):
            if "type" not in c:
                err(f"booking.components[{i}].type", "required")

    if op == "add_payment_to_supplier":
        pay = req.get("payment", {})
        for f in ("amount", "dueDate", "paymentMethod"):
            if f not in pay:
                err(f"payment.{f}", "required (offer methods from booking_payment_to_supplier_method_list)")
        if "paymentId" in pay and "paidDate" not in pay:
            err("payment.paymentId", "only valid together with paidDate")

    if op == "create" and "payment" in req:
        p = req["payment"]
        for f in ("tripId", "clientId", "subject", "invoiceFor", "total", "dueDate"):
            if f not in p:
                err(f"payment.{f}", "required")
        if p.get("invoiceFor") == "FEES" and "feeTypeId" not in p:
            err("payment.feeTypeId", "required for FEES (client_payment_configuration_view fee_types)")
        if p.get("processingCostPct") is not None:
            warn("payment.processingCostPct", "send only if the user stated a rate; omit for TripSuite CC/ACH processing")
        if "totalCharged" in p:
            err("payment.totalCharged", "never compute/send totalCharged; read it from the response")

    if op == "create" and "invoice" in req:
        inv = req["invoice"]
        actions = [s.get("clientAction") for li in inv.get("lineItems", []) for s in li.get("subItems", [])]
        if "REQUEST_PAYMENT" in actions and not inv.get("paymentMethodIds"):
            err("invoice.paymentMethodIds", "REQUEST_PAYMENT needs ≥1 method id (trip_invoice_payment_method_list; include all by default)")
        if actions and "REQUEST_PAYMENT" not in actions and inv.get("paymentMethodIds"):
            warn("invoice.paymentMethodIds", "authorization/document-only invoices should use []")
        for i, li in enumerate(inv.get("lineItems", [])):
            if li.get("bookingId") and li.get("clientPaymentId"):
                warn(f"lineItems[{i}]", "a line item normally references a booking OR a client payment, not both")
        if inv.get("memo") or inv.get("terms"):
            warn("invoice.memo/terms", "client-facing text: polished, no internal notes or sensitive data")

    if op == "add_member":
        pass

    health = req.get("health")
    if isinstance(health, dict):
        warn("health", "complete block: omitted fields are CLEARED. Make sure it contains everything you want to keep")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if src == "-" else open(src).read()
    data = json.loads(raw)
    args = data.get("arguments", data) if isinstance(data, dict) else data
    walk(args)
    for r in find_requests(args):
        semantic(r)
        # profile save puts sections at top level of arguments
    for line in errors + warnings:
        print(line)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
