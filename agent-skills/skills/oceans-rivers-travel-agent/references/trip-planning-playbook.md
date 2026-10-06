# Trip planning playbook

How to help advisors plan, recommend, and propose. The agency's documented process is: **a detailed consultation, then a proposal with hand-picked recommendations**, followed by door-to-door support. Everything below that goes beyond that is a **suggested working method** and general expertise: label it as such, and keep volatile facts as **[Verify]** (see `sourcing-and-accuracy.md`).

## Contents
1. [Planning flow](#1-planning-flow)
2. [Start from what we already know](#2-start-from-what-we-already-know)
3. [Consultation checklist](#3-consultation-checklist)
4. [Specialty considerations](#4-specialty-considerations)
5. [Choosing suppliers (Virtuoso preferred)](#5-choosing-suppliers-virtuoso-preferred)
6. [Presenting recommendations](#6-presenting-recommendations)
7. [Building a proposal](#7-building-a-proposal)
8. [After the client says yes](#8-after-the-client-says-yes)
9. [Pre-departure and in-trip support](#9-pre-departure-and-in-trip-support)
10. [Group voyages](#10-group-voyages)

---

## 1. Planning flow

```
Know the traveler → Consult → Shape options → Present 2–3 → Refine → Proposal → Book → Prepare → Support
   (TripSuite)      (advisor)   (expertise)    (labelled)              (template)   (TripSuite)  (tasks)
```

Your role is to speed up the advisor's steps: pull what's known, suggest questions, structure options, draft the proposal, and log the booking and tasks in TripSuite once they say go.

## 2. Start from what we already know

Before suggesting anything for an existing client, check TripSuite. First follow the hand-off in `tripsuite-integration.md` (read the `tripsuite-mcp` skill; UUID first, otherwise search and **confirm the match**):

- **Profile preferences:** `client_profile_view` with `sections=[preferences,programs]` (add `health` / `passports` only when the task needs them, e.g. dietary or mobility needs, passport validity for a polar or visa-sensitive trip).
- **History:** `trip_search clientId=…` (destinations, dates, how often they travel) and `booking_search clientId=…` with `expand=supplier` (which lines/hotels they've used).
- **Open items:** `task_search` for the client or trip; unpaid client payments if relevant.
- **Group context:** `group_search clientId=…` for family or friend groups traveling together.

Summarize it briefly: "From TripSuite: three trips in the last four years, mostly river cruises; prefers aisle seats; hasn't done an expedition voyage." If the data isn't there, say "none recorded". Don't guess preferences.

## 3. Consultation checklist

Suggested questions to cover (advisor decides which apply; don't interrogate). Group them and ask 3–5 at a time.

- **Who & why:** travelers (ages, mobility/health considerations, first-time vs experienced cruisers), occasion, what a perfect trip feels like.
- **When:** dates or season, flexibility, trip length, school/work constraints.
- **Where & what:** regions, bucket-list places, activity level (relaxed, active, wildlife, culture, culinary, photography).
- **Style:** ship size and ambiance, level of luxury, formal vs relaxed, all-inclusive preference, cabin type, dining preferences.
- **Budget:** comfortable range, what's worth splurging on.
- **Beyond the voyage:** pre/post hotel stays, private touring, special experiences, air needs and departure city, loyalty programs.
- **Practicalities:** passports and visas, travel insurance, dietary/medical needs (sensitive; only record what the traveler volunteers and the advisor needs).

For a returning client, **skip what TripSuite already answers** and ask only what's changed.

## 4. Specialty considerations

*General travel knowledge, not agency data. These are prompts for what to clarify and verify, not facts to quote. Confirm all specifics with the supplier.*

**Small-ship / yacht cruising** (e.g. the agency's focus on small luxury ships and sailing yachts)
- Clarify what matters: intimacy, ports big ships can't reach, dining/inclusions, onboard style.
- Verify: passenger capacity, itinerary and port access, inclusions (excursions, gratuities, drinks), cabin categories, current offers and Virtuoso amenities.

**River cruising**
- Clarify: rivers/regions, season, preferred pace, mobility (ships, gangways, tours).
- Consider and verify: seasonal conditions such as water levels or festive-market timing, whether the itinerary operates as sold, included excursions, and pre/post stays in the embarkation city.

**Expedition and polar (Antarctica, Arctic, Greenland, Northwest Passage, Galapagos)**
- Clarify: wildlife and landscape goals, tolerance for weather-dependent plans, physical ability for landings, previous expedition experience.
- Consider and verify: operating season for the specific region, itinerary flexibility, ship ice class/capacity where relevant, gear and boot requirements, medical and evacuation insurance expectations, flight timing and buffer days, and landing/activity inclusions.

**Safari and land touring**
- Clarify: species and ecosystems of interest, style (camp, lodge, private), pace, group vs private.
- Consider and verify: timing relative to wildlife patterns, internal flights/baggage limits, health requirements, and combined pre/post voyage stays.

**Ocean cruising (premium and luxury lines)**
- Clarify: itinerary vs destination priority, ship size and style, port intensity vs sea days.
- Verify: current itineraries, inclusions, and cabin availability.

**Custom, tailor-made touring**
- Clarify the "hero experience" the traveler will remember (e.g. a private tasting, a special guide) and build the trip around it.
- Check for ties to the agency's documented relationships: hoteliers, in-destination partners, specialty tour providers. Say "the agency has relationships" only in those general terms; don't name partners without a source.

**Departing from Calgary** (the agency is Calgary-based; clients are often too, but check)
- Long itineraries usually involve connections and time-zone changes; discuss arrival buffer before embarkation and whether to add a pre-cruise night. Verify routings and schedules in the booking system.

## 5. Choosing suppliers (Virtuoso preferred)

1. Identify what the traveler wants (§3) and shortlist suppliers by **fit** first.
2. **Verify preferred-partner status on virtuoso.com** (`virtuoso-partner-lookup.md`): one supplier at a time, using the Playwright MCP or another browser tool, and keep the link and date. Check the agency's saved record in `assets/preferred-partners-template.md` for anything already verified (note its date), and TripSuite supplier tags only as a secondary hint (confirm the tagging convention with the user).
3. Where Virtuoso lists the supplier as preferred, favor it and say so: "Virtuoso lists X as a preferred supplier (checked <date>)". Note scope if the page shows one (programs can be regional).
4. Where you **couldn't verify** (blocked, login wall, page not found), say so: "I couldn't verify Virtuoso status from here; worth confirming before presenting."
5. Use TripSuite to see **our history** with a supplier: `supplier_search name=…` → `booking_search supplierId=…` (volume, past clients) and commission information (expected vs received). Report as data, not as a recommendation to the client.
6. Don't promise perks. Perks shown on Virtuoso pages are descriptive; phrase as "Virtuoso lists these perks for X; confirm the exact amenity and eligibility for this booking".

## 6. Presenting recommendations

Offer **2–3 options** and a clear top pick. For each:

- **What it is** (one line) and **why it fits** this traveler (tie to their stated preferences or past trips: label the source).
- **What's special** (experience, ship style, destination).
- **Trade-offs** (honest, e.g. more travel time, weather dependence).
- **To verify:** pricing, availability, dates, Virtuoso status/amenities, entry requirements.

Format as a compact comparison table when comparing options, followed by "My top pick and why". Keep enthusiasm genuine and specific, not generic superlatives.

## 7. Building a proposal

Use `assets/proposal-template.md` (logo at `assets/logo.png`). Rules:

- Fill from **sourced facts**: client names, dates, and supplier details from TripSuite or the quote the advisor provides.
- **Prices, availability, inclusions, and amenities only from a supplier quote or TripSuite**; otherwise leave **[Verify]** placeholders for the advisor.
- Include the agency's service promise in its documented terms (door-to-door support, VIP perks and enhanced problem resolution where applicable), and **planning/service fees only if applicable and agreed**; the agency discusses fees up front and doesn't charge flat booking fees.
- Keep client-facing text free of internal notes, commission details, and sensitive profile data.
- Deliver as a document when the user wants something to send or keep (see the file-creation rules); otherwise draft in the reply.

## 8. After the client says yes

Offer to set it up in TripSuite using `tripsuite-mcp`:
1. Confirm the **client** (UUID, or search then confirm) and **trip** (create if needed; check for duplicates/overlapping trips).
2. Build the **booking** from the supplier confirmation (`booking_source_extract` first). Ask: who pays the supplier (client or agency), commissionable or not, payment schedule. **Never assume** these.
3. Create **tasks** (final payment dates, documents, follow-ups, passport expiry checks).
4. If fees apply, create the client payment/invoice as agreed.

Everything goes through the hand-off and confirmation rules in `tripsuite-integration.md` and the `tripsuite-mcp` skill (read its `references/money-flows.md` before any money write).

## 9. Pre-departure and in-trip support

Suggested checklist to run from TripSuite data (flag, don't assume):
- Final payments due vs paid (supplier payments and client payments).
- Booking confirmation numbers present on all confirmed bookings.
- Passport validity and visa/entry requirements **[Verify with official sources]**.
- Travel insurance recorded; special requests (dietary, mobility, celebrations) passed to suppliers.
- Open tasks and upcoming departures (`trip_search` window; `task_search`).
- Documents sent; emergency contact on file (profile `personal` section).

The agency promises door-to-door support and enhanced problem resolution through its supplier relationships; when a trip has a problem, help the advisor gather the facts from TripSuite (booking, supplier, confirmation numbers, payments) and draft the supplier escalation.

## 10. Group voyages

The agency hosts group voyages (the profile mentions advisors hosting). To support them: use TripSuite groups and tags to track participants (`group_search`, `trip_search tag=`), pull each traveler's trip/booking/payment status, and summarize who is confirmed, who owes a payment, and what's outstanding. Don't state group pricing, perks, or host arrangements without a source.
