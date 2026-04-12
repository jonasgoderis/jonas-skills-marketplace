# The Traveler — Skill Design

## Overview

A Claude skill that replaces the existing `holiday-planner`. Guides collaborative trip planning from a vague idea to a complete itinerary with interactive visual output.

## Traveller Profile

Baked into the skill — never ask the user to repeat:

- **Group:** Couple, no kids
- **Into:** Hiking, rafting, kayaking, hidden beaches, wildlife spotting (binoculars), photography, old towns & historic cities, local food & drink, off-the-beaten-path spots
- **Not into:** Beach resorts, tourist traps, rushed schedules
- **Accommodation:** Cozy stays (B&Bs, boutique hotels, charming cottages)
- **Pace:** Balanced — active days with time to enjoy the place

## Planning Flow

### Phase 1: Trip Brief

Ask for: destination, duration, dates, must-sees (optional), budget range (optional).

### Phase 2: Region Research

Deep web research focusing on:
- Adventure activities (hikes with difficulty/duration, water sports, wildlife viewing spots, photo opportunities)
- Culture (old towns, historic cities, charming villages, museums, local events)
- Local insider knowledge (blogs, forums, local tips — not just mainstream guides)
- Practical logistics (road conditions, seasonal closures, gear needed)

Present 6-10 candidate base locations with a suggested route. Wait for user to pick/drop/adjust.

### Phase 3: Stop Selection & Route

Ordered stops with recommended nights, driving distances/times, total duration check. Adjust until the route fits.

### Phase 4: Deep Dive per Stop

For each confirmed stop, deep web research and present:

- **Adventures:** Hikes (difficulty, duration, trail links), water sports, wildlife spots, photo opportunities
- **Culture:** Old towns, historic sites, museums, local events
- **Food & drink:** Authentic restaurants, markets, local specialties
- **Logistics:** Road conditions, parking, booking requirements, gear needed, best time to visit

Every activity and recommendation includes clickable links to external sources (trail guides, booking sites, blog posts, Google Maps).

Present one stop at a time. Wait for feedback before next.

### Phase 5: Final Output

Two deliverables:

#### Interactive (React artifact or standalone HTML)

**Environment detection:** Generate a React artifact in Claude Desktop/web. Generate a standalone HTML file (React via CDN + Leaflet + Tailwind) in Claude Code.

**Layout:**

1. **Route Map (top)** — Leaflet map with emoji pins for each stop, connected by a route line with directional arrows showing travel direction.

2. **Vertical Timeline (middle)** — Vertical line with dots (circles with emoji). Dates on the left, stop name + nights + drive time on the right. Click a dot to scroll to that stop's detail section.

3. **Stop Detail Sections (bottom)** — One section per stop containing:
   - Days/nights at this stop
   - Activity cards/options with duration tags, organized by category (adventures, culture, food & drink, wildlife)
   - Clickable links to detailed external information
   - Practical logistics

#### Markdown Summary

Flat markdown version of the same content for quick reference. Route overview, then stop-by-stop details.
