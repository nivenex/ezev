# Business analysis and reporting

The assistant also helps the agency **scale, optimize, and stay competitive**: market analysis, financial projections, growth insights, SWOT, revenue models, competitor benchmarking, and step-by-step implementation plans. This is Tier 5 in `sourcing-and-accuracy.md`: **frameworks and reasoning are yours; numbers come from TripSuite or the user; assumptions are always explicit.**

For how to pull and aggregate TripSuite data (revenue basis, commission, pipeline, supplier reviews, monthly report), **read the `tripsuite-mcp` skill first** (see `tripsuite-integration.md`), then its `references/workflow-patterns.md`. TripSuite has no analytics endpoints, so every figure is derived from searches you run and state.

## Contents
1. [Working method](#1-working-method)
2. [What the data can and can't tell you](#2-what-the-data-can-and-cant-tell-you)
3. [SWOT](#3-swot)
4. [Revenue model](#4-revenue-model)
5. [Projections](#5-projections)
6. [Competitor benchmarking](#6-competitor-benchmarking)
7. [Market analysis](#7-market-analysis)
8. [Growth and implementation plans](#8-growth-and-implementation-plans)
9. [Presenting results](#9-presenting-results)
10. [Guardrails](#10-guardrails)

---

## 1. Working method

1. **Clarify the question and decision.** What will this inform? Time horizon? Which definition of revenue/success? Ask one focused question if it truly changes the answer; otherwise state a default and proceed ("Assuming a 12-month view of confirmed bookings by travel date").
2. **Pull the facts** from TripSuite (parallel calls). Record scope: window, basis, currency, statuses included, record counts, any truncation.
3. **Separate** (a) what the data shows, (b) the agency profile facts, (c) your assumptions, (d) your interpretation.
4. **Apply the framework**, label hypotheses as hypotheses, and say how each could be tested with data.
5. **Recommend** next steps with rationale, owner placeholders, and measurable KPIs.
6. **Flag limits:** missing data, small samples, things TripSuite doesn't record.

## 2. What the data can and can't tell you

| Question | Derivable from TripSuite? | How / caveat |
|---|---|---|
| Booked volume (sales) | Yes | Sum of booking totals (use the home-currency fields where available) over a stated window and date basis (booked, created, or travel date) |
| Commission expected / received / overdue | Yes | Booking commission fields and commission records; check the actual status values in the data before defining "pending" or "overdue" |
| Fee income | Yes | Client payments of type FEES (billed vs paid) |
| Mix by supplier / supplier type | Yes | Bookings with supplier expanded |
| Pipeline and conversion | Partly | Trips by pipeline stage (stage names are agency-specific); conversion is derived from stage counts, and only as good as how consistently stages are used |
| Repeat vs new clients | Partly | Client creation dates vs trip history; derive and label it |
| Advisor performance | Partly | Bookings/commission by advisor (note splits); payouts via statements if the user has access |
| Forecast | **No** | No forecast tool; build scenarios from booked data and stated assumptions |
| Client lifetime value | **No** | Not stored; can be derived approximately and labelled |
| Market size, competitor data, industry growth | **No** | Not in TripSuite or the agency profile; needs user-supplied sources |
| Customer satisfaction / reviews | Only as stated in the profile | The profile lists a "5 stars" rating, undated and unsourced |

Accounting basis and currency: check the organization settings (`organization_view`) rather than assuming, and keep commission timing in mind (booking date ≠ commission due date ≠ received date).

## 3. SWOT

**Strengths: documented in the agency profile** (cite as "from the agency profile"):
- Full Virtuoso member agency with **Virtuoso Cruise Icon** status (top 1% of global cruise sales advisors) and preferred-partner status with several cruise lines.
- Clear **specialization**: ocean, river, small-ship, expedition; plus polar, safari, and custom land touring.
- **Senior, experienced team**: owner with 30 years in the industry (17 as owner/GM), awards listed, committee roles at Virtuoso; an advisor with 15 years and 100+ voyages.
- **First-hand experience** across a wide range of lines and ships (200+ and 100+ voyages respectively).
- Stated service promise: personal service, curation, VIP perks, enhanced problem resolution, door-to-door support, no flat booking fees.

**Weaknesses, Opportunities, Threats: hypotheses, not facts.** The profile doesn't document these, so don't state them as true. Offer candidate hypotheses with the data check that would confirm or refute each, and ask the owner for their view:

| Hypothesis (label as such) | How to test with TripSuite |
|---|---|
| Small team → capacity or key-person concentration | Bookings/commission by advisor over time; open tasks per advisor |
| Supplier concentration risk | Share of booked volume and commission by supplier |
| Seasonality / uneven cash flow | Booked volume and commission received by month |
| Under-developed segments (e.g. safari, land tours, hotels) | Booking mix by supplier type vs the stated specialties |
| Opportunity: repeat and referral business | Share of trips from returning clients; client creation vs trips |
| Opportunity: hosted group voyages | Group/tag-based trips and their volume and margin |
| Opportunity: fee income on complex custom trips | FEES client payments vs trips needing heavy planning |
| Overdue commissions tying up cash | Pending/overdue commissions by supplier |
| Threats: market, competition, supplier policy changes | **Not in the data.** Ask the user, or label as general market observation |

Present as a 2×2 or four short lists. Mark each item **[Documented]**, **[Data shows]**, or **[Hypothesis]**.

## 4. Revenue model

Documented agency income logic: the agency **doesn't charge flat booking fees**; **planning/service fees** may apply to select components and are discussed up front; supplier **commission** is tracked on bookings. If the user mentions other income (e.g. supplier overrides or incentives, hosted-group revenue), include it as stated by them and don't assume any.

Simple driver model:

```
Revenue = Commission income + Fee income (+ other income the user specifies)
Commission income = Σ over bookings ( booked value × commission % ), recognized per the agency's basis/timing
Fee income        = Σ planning/service fees billed (or collected, per basis)
Booked value      = # bookings × average booking value
```

Levers to explore (each measurable): number of new clients, repeat rate, bookings per client, average booking value, supplier/segment mix (commission % differs), fee uptake on complex trips, pipeline conversion by stage, time from final payment to commission receipt.

State clearly which of these you measured, which you assumed, and which you can't observe.

## 5. Projections

There is no forecast tool; build a transparent, assumption-driven projection.

1. **Baseline:** what's already booked: confirmed bookings departing in the horizon, expected commission by due date, fees billed/due. (From TripSuite; precise.)
2. **History:** same period last year(s) with the same definitions (From TripSuite).
3. **Scenarios:** conservative / base / optimistic, each defined by explicit drivers (e.g. new-booking volume vs last year, average booking value change, mix shift, conversion). Keep to 2–4 drivers.
4. **Show the math** in a table so the advisor can edit assumptions.
5. **Label:** "Projection based on the assumptions above (not a record)." Never present a projected figure as retrieved data.
6. **Sensitivity:** note which assumption moves the result most.
7. **Caveats:** timing of commission receipts, cancellations/refunds, currency, and the small-sample risk for a small agency.

Example layout:

| | Conservative | Base | Optimistic |
|---|---|---|---|
| New-booking volume vs last year | *assumption* | *assumption* | *assumption* |
| Avg booking value change | *assumption* | *assumption* | *assumption* |
| Commission % (mix) | *from history* | *from history* | *assumption* |
| **Projected commission** | *computed* | *computed* | *computed* |

## 6. Competitor benchmarking

You hold no verified competitor data. **Don't invent competitor names, prices, sizes, or reputations.**

1. Ask the user **who** to benchmark and **what sources** they have (competitor websites, quotes, brochures, review pages they paste in).
2. Compare on dimensions: specialization and depth, supplier access/status (e.g. Virtuoso tiers), service model and fees, advisor experience, group/hosted offerings, proposal quality and speed, digital presence, reputation (as supplied).
3. For the agency side, use the **agency profile** and TripSuite data, cited.
4. For the competitor side, use **only what the user provides**, cited. General observations about the market are allowed if labelled "general market observation, not verified".
5. Output a side-by-side table with a "source" column, then **gaps and differentiators**, then actions.

## 7. Market analysis

Use general reasoning about trends in luxury, small-ship, expedition, and river travel **only as labelled general knowledge**, hedged and without statistics. For anything quantitative (market size, growth rates, demand shifts), ask the user for a source or say it needs a source. Tie any implication back to agency data ("TripSuite shows X; the general trend would suggest testing Y").

## 8. Growth and implementation plans

Give step-by-step plans in this structure:

1. **Objective** (specific, measurable) and **why now** (cite data).
2. **Initiatives** (3–5), each with: what, why (data/hypothesis), who (**owner: [to assign]**), effort.
3. **Timeline:** phases (e.g. 30/60/90 days or quarterly).
4. **KPIs** measurable from TripSuite (booked volume, commission expected/received/overdue, fee income, pipeline by stage, repeat-client share, tasks overdue) with baseline values pulled from data.
5. **Risks and dependencies**, and **what to do if a KPI misses**.
6. **Review cadence** (e.g. monthly report using the TripSuite workflow patterns).

Offer to turn the plan into TripSuite tasks (with the user's confirmation, using `tripsuite-mcp`).

## 9. Presenting results

- **Lead with the headline**, then the scope line (window · basis · currency · record counts), key numbers, flags, and recommended actions.
- Use tables for comparisons; short bullets for insights; one chart-worthy comparison at most if a visual is requested.
- Use names, not IDs; label sources; mark assumptions and hypotheses.
- Offer a drill-down menu at the end (e.g. by supplier, by advisor, by month).
- For deliverables the user wants to keep or share (a report, deck, or spreadsheet), follow the file-creation conventions available in the environment.

## 10. Guardrails

- **Never** present an estimate, hypothesis, or general market observation as data.
- **Never** invent competitor information, market statistics, or agency performance figures.
- Keep client-identifying details out of aggregate reports unless the user asks for client-level detail.
- Don't give personalized investment, tax, or legal advice. This is business analysis; suggest the agency's accountant or advisor for those.
- When the data is too thin for a conclusion (e.g. a handful of bookings), say so and show ranges rather than false precision.
