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

## Planning Phases

Work through these phases in order. Present results after each phase and wait for user approval before continuing. The user may ask to revisit earlier phases at any time.

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
- Route summary: A (X nights) → B (Y nights) → C (Z nights)
- Total duration check — flag if it doesn't fit available days
- Suggest adjustments if needed (drop a stop, reduce nights)

Wait for user to adjust until the route feels right.

### Phase 4: Deep Dive per Stop

For each confirmed stop, use WebSearch to do deep research. Search for: "[stop] best hikes trails", "[stop] wildlife spotting", "[stop] kayak rafting", "[stop] hidden gems blog", "[stop] local restaurants authentic", "[stop] old town walking", "[stop] practical travel tips".

Present for each stop:

**Adventures**
- Hikes with difficulty rating, duration, distance, and links to trail guides
- Water sports (rafting, kayaking) with operators/links if applicable
- Wildlife spotting locations — what animals, best time of day, best season
- Photography spots — landscapes, animals, viewpoints
- Hidden beaches or natural swimming spots

**Culture**
- Old towns, historic quarters — what to see, why it's special
- Historic sites, castles, ruins
- Museums or local events worth visiting
- Charming villages nearby

**Food & Drink**
- Authentic local restaurants (not tourist traps)
- Markets, food specialties, local drinks
- Must-try dishes for the area

**Logistics**
- Best neighbourhood/village to stay in
- Road conditions and parking
- Booking requirements or reservations needed
- Gear needed (hiking boots, water shoes, etc.)
- Best time to visit specific spots

**Every recommendation must include a clickable link** to an external source: trail guide, Google Maps, booking site, blog post, or official page.

Present one stop at a time. Wait for user feedback before moving to the next.

### Phase 5: Final Output

Generate two deliverables:

#### 1. Interactive Itinerary

Generate a React artifact (in Claude Desktop/web) or a standalone HTML file (in Claude Code, using React via CDN + Leaflet via CDN + Tailwind via CDN).

**Layout:**

**Route Map (top)**
- Leaflet map showing all stops as pins with emoji markers matching the stop character
- Stops connected by a route polyline with directional arrows showing travel direction
- Map auto-fits to show the full route

**Vertical Timeline (middle)**
- A vertical line with dots at each stop
- Each dot is a circle with an emoji representing the stop (🏔️ mountain, 🏛️ city, 🏖️ coast, 🌲 forest, etc.)
- Left side: dates (arrival — departure)
- Right side: stop name, number of nights, drive time from previous stop
- Clicking a dot smooth-scrolls to that stop's detail section below

**Stop Detail Sections (bottom)**
- One expandable section per stop
- Header: stop name, dates, nights
- Activity cards organized by category (Adventures, Culture, Food & Drink, Wildlife)
- Each card shows: name, duration/difficulty tag, short description, external link
- Logistics section with practical info

**Styling:** Clean, modern, easy to read. Use category colors to distinguish adventures/culture/food/wildlife.

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
### Adventures
- [Name] — [difficulty] — [duration] — [link]
### Culture
- [Name] — [description] — [link]
### Food & Drink
- [Name] — [description] — [link]
### Logistics
- [Practical details]

## Stop 2: [Base Name] — X nights
...

## Don't Miss — Top 5 Highlights
[The absolute best experiences across all stops]
```
