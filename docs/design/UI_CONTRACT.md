# UX/UI implementation contract (approved concept, not official UI Kit)

## Visual system
Approximate BIOCAD style: navy `#0C204D`, green `#43B880` (or consistent selected green token), white `#FFFFFF`, cool light gray `#F4F6FB`, blue for booked FreeDesk; charcoal text, corners approx 8–16 px, strong contrast, compact whitespace. Exact BIOCAD design tokens, font license and logo usage must be verified against official supplied assets; **do not claim corporate compliance** without those assets. Use reusable React components and CSS variables; responsive layouts: desktop left employee search/filters + center map + right drawer; tablet map with collapsible side/bottom details; mobile scrollable/zoomable map + bottom sheet and bottom navigation. Keep font readable.

## Floor plan
At least 2 floors, floor 2 detailed with >=24 desk nodes and >=3 meeting rooms; room outlines, walls, doors, passage, kitchen, bathroom, recreation and window/HVAC decorations; SVG pan/zoom + fit; keyboard accessible desks; legend and last-updated status. Do not use a bitmap as the interactive map: create SVG positions backed by API coordinates. Individual rooms and workstations have stable ids.

## Occupancy colors and avatars
- Green: available FreeDesk for chosen period. No occupant avatar.
- Light blue: FreeDesk reserved by other user whose booking overlaps selected period, render associated fictional employee avatar (or initials fallback).
- Gray plus lock: permanent/dedicated; show assignment owner avatar when permissible; never bookable as FreeDesk.
- Selected: navy outline independent of true status; own booking distinguishable (label/border).
- If period overlaps 2+ distinct bookings of same desk, render avatar stack / `+N` and detail timeline in drawer; do not show one avatar as if occupant for entire range. Do not show outdated avatars during new request (pending indicator, cancel prior request or reject stale response).
- Selection panel: name, job, department, avatar, desk ID, space type, exact booking start/end ISO shown MSK; multiple ordered entries; booking action only for fully available requested interval; if no photo render initials with accessible label. Avoid PII in untrusted LLM paths.
- Dedicated avatar and future reservation mean **assigned/reserved**, not an actual presence sensor. Explain in UI.

## Time scenario for acceptance
Demo fixture 2026-11-16: D-03 Maria Sokolova 10:00–12:00; FREE 12:00–14:00; Pavel Gromov 14:00–16:00. Integration + E2E must cover day 09:00–17:00 (multiple avatars), 10:00–12:00, 12:00–14:00, 14:00–16:00. Adjacent periods legal under `[start,end)`.

## Booking states
Loading/skeleton, missing floor, no availability, unavailable server, booking conflict from racing user, success, cancel confirmation/success, AI primary, AI fallback (warning), AI unavailable (manual form still available). Confirmation screen displays exact office/floor/desk/date/start/end, human authorizes action before any write.

## Recommendation/quiz/feedback (P1/P2)
Search for window, away from HVAC, floor <=2, quiet zone, kitchen/rail/restroom proximity with clear verified/demo attributes; ask for required missing time, rank only available desks. Optional 6-question comfort quiz, editable profile, ability to skip. Feedback after completed booking, liked/disliked reasons; previously liked desk offered only if currently available and explicitly confirmed.

## Release history UI
Separate `/releases` page, chronological SemVer, date, features/fixes, link to real PR/commit/test run and actual deployed version. Demo visual reference must not leak into production as fake history. If there are no releases, show correct empty state.

See `references/desktop/WB-16_desktop.png` and matching tablet/mobile variants and `references/calendar_scenarios/` for visual references.
