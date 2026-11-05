# drawio-conventions: long labels, covered icon labels and overlapping lines

Date: 2026-11-05

After release v1.16.0, the user reported three problems in real diagrams. This
document records the cause of each, the change, and how it was checked.

## 1. Long labels run over their shape

**Problem.** Labels on shapes and icons are often too long. They run over the
border of a box, or under an icon they reach the neighbouring shapes.

**Change.** A new rule in the Labels section of `references/house-style.md`:
split a long label over 2 lines with `<br>`, at a word boundary near the middle.
Use 3 lines only when 2 are not enough. If 3 lines do not fit, widen the shape,
shorten the label or move the detail into a note.

**Script.** `check_drawio.py` estimates the width of each label and warns when:

- a line of an icon label is wider than about 160 px (or 2.5 times the icon),
- a label in a box without wrapping is wider than the box,
- a wrapped label needs more lines than the box height allows, or more than 3,
- a single word is wider than the box.

**Calibration.** A render of test labels with `draw.io -x` showed about 5.5 px
per character at `fontSize=12`. The script uses 6 px, which leaves a small
margin. The note size rule now uses the same value; it said 7 px before.

## 2. Icon labels under a line, inside groups

**Problem.** In a diagram with groups, some icon labels were under a line.

**Cause.** draw.io draws a group together with everything in it, at the
group's own place in the file. A line on the page that comes after the group
is drawn over every icon inside it. The old rule and the old check only
compared an icon with the lines of the same parent, so this case passed.

A render confirmed it. With the line written after the group, the line runs
through the icon label. With the line written before the group, the label is
on top.

**Change.** Within each parent, edges come first, then groups, then the other
shapes and icons. An edge belongs to the parent of whichever end is drawn
later: a line from the page into a group goes inside the group, and a line
between two groups goes into the later one. A render showed why. With filled
groups and the lines on the page, the fill hides the lines. With each line
inside the group of its later end, the line shows on top of the fill and
under the icons.

The first version of this change required `fillColor=none` on every group.
The user said groups may have a fill, so the rule moved the edges into the
groups instead.

**Script.** It walks the cells in drawing order. It reports an icon as a
`FAIL` when an edge of its own parent, or of any parent around its group, is
drawn after it. It reports an edge that ends in a group but sits outside it:
a `FAIL` when the group has a fill (a group without `fillColor` gets draw.io's
white fill), and a `WARN` when it has none.

**Limits.** draw.io moves an edge back to the shared parent when someone
reconnects it in the app. The script then reports it. A line between two groups
is drawn over the earlier group, icons included, so the rule asks to route it
away from those icons. A line that only passes over a filled group, with no end
in it, disappears under the fill and must go around it.

## 3. Lines on top of each other

**Problem.** Two lines sometimes run along the same stretch, so one hides the
other. This is different from a crossing, which the line jump shows.

**Cause.** draw.io computes the routes when it draws. The XML holds only the
end shapes and any waypoints, so the file alone does not show an overlap. The
common causes are two edges in opposite directions between the same shapes,
several edges on one side of a shape, and two edges that pick the same corridor.

**Change.** A new spacing rule names those causes and their fixes. The script
now renders each tab to SVG with the installed draw.io app (`draw.io -x -f svg
-p <tab>`). The SVG holds each line as a path with the real route, marked with
`data-cell-id`. The script compares the straight stretches of every pair of
lines. A shared stretch of at least 10 px, closer than 4 px, is a `FAIL`. Lines
closer than 12 px are a `WARN`. `--no-render` skips this. Without draw.io the
script says the check did not run.

**Checked.** On the test diagrams, the check finds two edges in opposite
directions and the fan-out without waypoints. It passes the fan-out with
waypoints.

The skill description said the skill "does not render or export diagrams".
That is no longer true for the check, so it now says the skill does not export
diagrams to images for the user. The near-miss trigger case
`drawio-export-png` covers that sentence.

## Evals

New case `azure-group-long-labels`: icons in a resource group, lines that
cross the group, a long icon name and a webhook that runs opposite to a call.
Its graders check that no edge to a shape in the group stays on the page, that
no page-level edge comes after a group, and that no icon label has a line over 30 characters. A regex
cannot see overlapping lines, so the case relies on the script for those.

## Eval results

Model `claude-sonnet-5`, judge `claude-haiku-4-5-20251001`, 3 runs per case.

| Selection | Result | Cost |
| --- | --- | --- |
| Full `drawio-conventions` suite (13 cases), with the first group rule (`fillColor=none`) | 13/13 at 1.00 | $10.55 |
| `azure-group-long-labels` with the final group rule (edges inside the group) | 3/3 at 1.00 | $1.51 |

In the kept sandboxes of the second run, the agents fixed what the script
reported: a fan-out without waypoints and an icon written before its line.
One run hit the 300-second limit after it had written a passing file.

The render check did not run in any eval run. Inside the eval sandbox, draw.io
writes no SVG. The script then warns that overlapping lines were not checked,
as designed. So the overlap check is tested only on the test diagrams in this
document, not by the eval suite.
