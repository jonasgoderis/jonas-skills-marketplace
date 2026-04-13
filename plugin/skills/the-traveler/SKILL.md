---
name: the-traveler
description: Use when planning a holiday, trip, or vacation. Triggers on requests like "plan a road trip to Scotland", "city trip to Porto", "help me plan a holiday", "where should we go this summer", or any travel planning task. Guides the user through collaborative phased trip planning from destination idea to a complete interactive itinerary.
---

# The Traveler

Plan trips from a vague idea to a complete interactive itinerary through collaborative phased dialogue. Use WebSearch actively throughout every phase for up-to-date information, hidden gems, insider tips, and practical details.

## Traveller Profile

These preferences are always applied — never ask the user to repeat them:

- **Group:** Couple, no kids
- **Into:** Hiking, rafting, kayaking, hidden beaches, wildlife spotting (they carry binoculars), photography (especially animals and nature), old towns & historic cities, local food & drink, off-the-beaten-path spots
- **Not into:** Beach resorts, tourist traps, rushed schedules
- **Accommodation:** Cozy stays (B&Bs, boutique hotels, charming cottages)
- **Pace:** Balanced — active days with time to enjoy the place

## Activity Type Styles

Every activity card gets an automatic emoji badge based on its type:

| Type | Emoji | Badge Color |
|------|-------|-------------|
| Hiking | 🥾 | Green |
| Cycling / eBike | 🚴 | Lime |
| Kayaking | 🛶 | Cyan |
| Rafting | 🚣 | Blue |
| Sailing / Boat | ⛵ | Sky |
| Swimming / Beach | 🏊 | Aqua |
| Horse Riding | 🏇 | Brown |
| Climbing / Via Ferrata | 🧗 | Slate |
| Culture | 🏰 | Purple |
| Food | 🍽️ | Orange |
| Whisky / Drinks | 🥃 | Amber |
| Nature / Wildlife | 🌿 | Teal |
| Photography | 📸 | Pink |
| Drive-by | 📍 | Indigo |

Apply these automatically to every activity card in both the interactive itinerary and markdown output.

## Activity Diversity Checklist

When deep-diving a stop, **actively cover each of these broad buckets where the destination supports them** — do not default to hiking + culture only. This is a coverage goal, not a display taxonomy (use TYPE_STYLES for the badges).

- 🥾 **Hiking / walking** — trails at varied difficulty levels
- 🏰 **Culture & history** — castles, museums, battlefields, old towns
- 🍽️ **Food & drink** — local specialities, standout restaurants
- 🥃 **Regional specialty** — whisky in Scotland, wine in Tuscany, cheese in France, etc.
- 🌿 **Nature & wildlife** — spotting spots, reserves, unique ecosystems
- 🚴 **Adventure sports** — MTB/eMTB rental, rafting, canyoning, via ferrata, climbing
- 🛶 **On the water** — sea/loch kayaking, SUP, boat trips, sailing
- 📍 **Drive-by landmarks** — notable spots on the driving route between stops

If a destination genuinely doesn't support a bucket (e.g. no water in a desert region), skip it explicitly — don't pad with weak options.

## Formatting Rules

- **Day plans** must be structured arrays (one entry per day), never paragraphs
- **Activity descriptions** are concise: 2-3 sentences max for the "what"
- **Tips** render in a visually distinct box, separate from the description
- **No walls of text** — every card should be scannable in 5 seconds
- **Links** are always clickable, never bare URLs in prose

## Planning Phases

Work through these phases in order. Present results after each phase and wait for user approval before continuing.

**Iterative refinement is the norm.** Users bounce between phases constantly — changing nights, swapping stops, adding activities mid-discussion. When route changes happen, immediately cascade all downstream effects: date shifts, night redistributions, day plan updates, and accommodation adjustments. Don't wait for "phase completion" to propagate changes.

### Phase 1: Trip Brief

Ask the user for:
- **Destination** (region/country)
- **Duration** (total days available)
- **Time of year / dates**
- **Must-sees or must-dos** (optional)
- **Budget range** (optional — budget / mid-range / comfortable)

Proceed once you have at least destination and duration.

### Phase 2: Region Research

Use WebSearch extensively. Go beyond mainstream travel sites — search for blog posts, forum threads, and local recommendations.

Search for: "[region] hidden gems", "[region] off the beaten path", "[region] best hikes", "[region] wildlife spotting", "[region] adventure activities", "[region] charming old towns", "[region] local favorites blog".

Present:
- Overview of the region (geography, travel seasons, what it's known for)
- **6-10 candidate base locations**, each with:
  - Short pitch: why it's interesting, what's nearby
  - Type of experience: adventure / culture / nature / mix
  - Standout highlight (best hike, wildlife, old town, etc.)
- A suggested rough route connecting them
- Logistics flags (ferries, unpaved roads, border crossings, seasonal closures, gear needed)

Wait for user to pick bases, drop ones they don't want, or suggest additions.

### Phase 3: Stop Selection & Route

Based on user picks, propose:
- **Ordered stops** with recommended nights per stop
- **Driving distances/times** between consecutive stops
- **Drive-by highlights** for each leg — notable landmarks, viewpoints, or detours worth a brief stop on the drive between bases. Tag these as 📍 Drive-by. Search for: "[route from A to B] scenic stops", "[road name] points of interest", "[region] roadside attractions worth stopping".
- Route summary: A (X nights) → B (Y nights) → C (Z nights)
- Total duration check — flag if it doesn't fit available days
- Suggest adjustments if needed (drop a stop, reduce nights)

Wait for user to adjust until the route feels right.

### Phase 4: Deep Dive per Stop

For each confirmed stop, use WebSearch to do deep research.

**Search for experiences:** "[stop] best hikes trails", "[stop] wildlife spotting", "[stop] kayak rafting", "[stop] hidden gems blog", "[stop] old town walking".

**Search for practical logistics (just as important):** "[stop] [activity] booking advance reservation", "[stop] [wildlife] best time tide", "[stop] boat trip booking [year]", "[stop] ferry schedule", "[stop] parking [trailhead]". The most valuable research is practical: booking requirements, seasonal timing, tide dependencies, and operational details for each recommended activity.

Present for each stop:

**📍 Drive-by Highlights (from previous stop)**
- Landmarks, viewpoints, and brief detours on the drive in
- Listed as the first activities in this stop, tagged as Drive-by
- Include GPS coordinates or Google Maps links where possible

**Adventures**
- Hikes with difficulty rating, duration, distance, and links to trail guides
- **Cycling / eBike rentals** — scenic routes, rental shops with booking info, e-bike vs regular bike options, route difficulty and duration
- **Kayaking** — rental operators, guided tours vs self-guided, put-in locations, skill level required
- **Rafting** — operators, grade of rapids, season, advance booking requirements
- **Sailing / boat trips** — charter operators, skippered vs bareboat, day trips vs multi-day
- **Climbing / via ferrata** — routes, gear rental, guides
- **Horse riding** — trail rides, stables, experience level
- Wildlife spotting locations — what animals, best time of day, best season
- Photography spots — landscapes, animals, viewpoints
- Hidden beaches or natural swimming spots

For any rental or guided activity, explicitly search for: "[stop] [activity] rental booking", "[stop] [activity] operator reviews", "[stop] [activity] season price".

**Culture**
- Old towns, historic quarters — what to see, why it's special
- Historic sites, castles, ruins
- Museums or local events worth visiting
- Charming villages nearby

**🍽️ Where to Eat**
- **3-4 specific restaurant recommendations** per stop
- Each with: name, what it's known for, and when to go (e.g., "best for arrival evening", "grab pies for the beach", "book ahead for dinner")
- This is a dedicated section, separate from food-type activities

**Activity Card Format**

Every activity card has two distinct sections:
1. **Description** (the what) — 2-3 sentences max. What is it, why is it special, what will you see/experience.
2. **Tips** (the how) — rendered in a visually distinct box. Cover: parking, timing, booking requirements, what to combine it with, gear needed, and weather alternatives.

**🏠 Accommodation**
- Suggest specific area/neighbourhood to stay in and **why** (proximity to trailheads, walking distance to restaurants, views, etc.)
- Accommodation card with fields for: name, URL, notes, and a visual **BOOKED** / **PENDING** status badge
- Users fill these in iteratively as they book

**🗓️ Day-by-Day Plan**
- A structured array — one entry per day, never a paragraph
- Each entry: day label in bold, then the plan
- **Split by session (morning / afternoon / evening) when useful** — this makes busy days scannable instead of a wall of text
- Schema: `{day, text}` objects, where `day` may include session (e.g. "Tue morning", "Thu evening")
  - **Tue:** Arrive via Plockton, Corrieshalloch Gorge on the way. Settle in, evening walk to the harbour, dinner at [restaurant].
  - **Wed morning:** Hike to [trail] — leave early to avoid midges.
  - **Wed afternoon:** Kayaking out of [harbour], 2hr rental.
  - **Wed evening:** Fish & chips at [place], sunset walk.
  - **Thu:** Wildlife boat trip (book ahead). Drive to next stop via [drive-by highlight].

**⚠️ Stop Practical Tips**
- Rendered as a highlighted callout at the bottom of the stop section
- Area-wide advice: fuel up here (next station is X away), road conditions (single-track with passing places), mobile signal status, midge/weather warnings, grocery shopping reminders, nearest hospital/pharmacy

**Must-see Flagging**

Flag genuinely unmissable activities with an orange **MUST-SEE** badge — e.g., puffin colonies in June, dolphin watching at the right tide, a once-in-a-lifetime viewpoint. This helps users prioritize when they can't do everything. Use sparingly (2-3 per stop max).

**Every recommendation must include a clickable link** to an external source: trail guide, Google Maps, booking site, blog post, or official page.

Present one stop at a time. Wait for user feedback before moving to the next.

### Phase 5: Final Output

Generate two deliverables:

#### 1. Interactive Itinerary

Generate a React artifact (in Claude Desktop/web) or a standalone HTML file (in Claude Code, using React via CDN + Leaflet via CDN + Tailwind via CDN).

**Layout:**

**Header Image (top)**
- If the user provides a hero image URL, display it as a full-width banner
- Fallback chain: external URL → base64 embedded image (if user uploads locally) → gradient with trip title overlay
- Ask the user if they'd like to add a header image

**Route Map**
- Leaflet map showing all stops as pins with emoji markers matching the stop character
- Stops connected by a route polyline with directional arrows showing travel direction
- Drive-by highlights shown as smaller markers along the route
- Map auto-fits to show the full route

**Vertical Timeline**
- A vertical line with dots at each stop
- Each dot is a circle with an emoji representing the stop (🏔️ mountain, 🏛️ city, 🏖️ coast, 🌲 forest, etc.)
- Left side: dates (arrival — departure)
- Right side: stop name, number of nights, drive time from previous stop
- Clicking a dot smooth-scrolls to that stop's detail section below

**Stop Detail Sections**
- One expandable section per stop
- Header: stop name, dates, nights
- **Drive-by highlights** as the first cards, tagged with 📍
- **Day-by-day plan** as a structured list (one entry per day, day in bold)
- Activity cards organized by category with automatic emoji badges from TYPE_STYLES
- Each card has two sections: description (the what) and tips box (the how)
- **MUST-SEE** badge (orange) on flagged activities
- **Where to Eat** section with restaurant cards
- **Accommodation** card with name, URL, notes, and BOOKED/PENDING status badge
- **Stop Practical Tips** as a highlighted callout at the bottom

**Useful Links (bottom of itinerary)**
- A grid of clickable cards collecting all useful external resources
- Booking sites, official tourism pages, hiking route guides, ferry operators, tide checkers, weather services, etc.
- Accumulated from all research throughout the phases

**Styling:** Clean, modern, easy to read. Use category colors and emoji badges to distinguish activity types. Tips render in a visually distinct box. Day plans as structured arrays, never paragraphs.

#### 2. Markdown Summary

Save a flat markdown file to the current working directory as `YYYY-MM-DD-[destination].md`.

Structure:

```
# [Trip Name] — [Date Range]

## Overview
- Route: A → B → C → D
- Duration: X days / Y nights
- Total driving: ~Z km
- Budget estimate: €XXX - €XXX

## Packing Tips
[Tailored to destination, season, and planned activities]

## Stop 1: [Base Name] — X nights

### 📍 Drive-by Highlights (from previous stop)
- [Landmark] — [why it's worth stopping] — [link]

### 🗓️ Day Plan
- **Tue:** [Structured day entry]
- **Wed:** [Structured day entry]

### 🏠 Accommodation
- **Name:** [Name] | **Status:** BOOKED / PENDING
- **URL:** [link] | **Notes:** [notes]

### Adventures
- 🥾 [Name] — [difficulty] — [duration] — [link]
  - **Tips:** [parking, timing, gear, weather alternatives]
- 🌿 [Name] — MUST-SEE — [description] — [link]
  - **Tips:** [booking requirements, best time, what to combine with]

### Culture
- 🏰 [Name] — [description] — [link]

### 🍽️ Where to Eat
- [Restaurant] — [known for] — [when to go]
- [Restaurant] — [known for] — [when to go]

### ⚠️ Practical Tips
- [Fuel, road conditions, signal, weather, groceries]

## Stop 2: [Base Name] — X nights
...

## Don't Miss — Top 5 Highlights
[The absolute best experiences across all stops, with MUST-SEE badges]

## 🔗 Useful Links
- [Booking site] — [link]
- [Tourism page] — [link]
- [Ferry operator] — [link]
- [Tide checker] — [link]
- [Hiking guides] — [link]
```
