# drawio-conventions: second round of layout feedback

Date: 2026-11-03

After release v1.15.0, the user reviewed new diagrams and asked for four
changes. This document records each change, the decision behind it and how it
was checked.

## 1. Several lines on one side of a shape

**Problem.** When several edges leave or enter the same side of a shape, they
all start at the middle of that side. They overlap and look like one line.

**Options.** There were two ways to spread them:

- Fixed exit points (`exitY=0.25`, `0.5`, `0.75`). These move with the shape,
  but rule A forbids fixed points.
- One waypoint per edge, at its own height within the side. Rule A stays as it
  is.

**Decision.** The user chose waypoints.

**How draw.io handles it.** I read the router code in the installed draw.io app
(`app.asar`). An orthogonal edge with waypoints switches to the segment router
(`orthPointsFallback` is on). That router leaves the shape at the height of the
first waypoint, when that height lies within the shape. A test diagram rendered
with `draw.io -x -f png` confirmed it:

- Without waypoints, three edges start at the same point. Draw.io even routes
  two of them through the middle target.
- With one waypoint per edge, at 1/4, 1/2 and 3/4 of the source height, each
  line starts at its own point and ends straight at its target's centre.
- A second waypoint on the target's centre line changes nothing.

**Drawback, and the fix.** Waypoints normally stay in place when someone drags
a shape. The style key `followTerminals=1` makes draw.io move them along. The
code (`getFollowedEdgePoints`) confirms the key exists. I did not test it by
dragging a shape in the app.

**Changes.** A new spacing rule in `references/house-style.md`, and a new
warning in `scripts/check_drawio.py` when two edge ends meet one side of a
shape within 10 px of each other.

## 2. Spacing between 80 and 120 px

**Problem.** A fixed minimum of 120 px makes simple diagrams large and empty.

**Change.** The gap is now 80 to 120 px. 80 px is the minimum. The agent picks
a wider gap where several lines meet a shape, where lines run side by side, or
where lines carry labels. The script warns below 80 px.

## 3. Icon labels always under the icon

**Problem.** One icon had its label on the right.

**Cause.** Of the 2,290 style strings that `--find` prints from draw.io's own
code, 448 set no label position, which puts the label on the picture. Thirteen
put it to the right. An agent that copies such a string gets the wrong position.

**Change.** A new row in the house-style table sets
`verticalLabelPosition=bottom;verticalAlign=top;labelPosition=center;align=center`
on every icon. The script reports an icon with a label elsewhere as a `FAIL`.

## 4. Notes sized to their text

**Problem.** All notes had the same, large size, whatever their text.

**Change.** A new Labels rule: estimate the width from the longest line (about
7 px per character plus 20 px, at most about 300 px) and the height from the
number of lines (about 18 px per line plus 20 px). Add `autosize=1`, so draw.io
resizes the note when someone edits its text. The script warns when a note is
more than twice as large as its text needs.

## Evals

- New case `gateway-fan-out-notes`: one gateway with four outgoing edges and
  two notes of very different length. Its graders check for waypoints with
  `followTerminals=1`, for no fixed points, and for `autosize=1` on a note.
- New grader `icon-labels-above-lines/graders/06-icon-labels-below.md`.
