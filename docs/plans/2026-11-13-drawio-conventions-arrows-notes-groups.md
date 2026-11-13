# drawio-conventions: one arrow per direction, fixed notes, groups and lines through labels

Date: 2026-11-13

After release v1.17.0, the user reported four problems in real diagrams. This
document records the cause of each, the change, and how it was checked.

## 1. Lines still overlap

**Problem.** Lines still end up on top of each other, and lines run through
labels. The user confirmed these two kinds. A line through a box without a
label was not part of the report.

**Cause.** The render check from v1.17.0 finds lines on top of each other, but
nothing checked a line against a label. Lines through labels therefore passed.
The overlap check also does nothing when draw.io cannot render, for example in
a sandbox. The skill then only asked to mention that in the report.

**Change.** The script now reads the label boxes from the render. After each
HTML label, draw.io writes a fallback image with the exact position and size of
the rendered text. The script narrows a wrapped label's box to the estimated
text width and tests every straight stretch of every other line against it. A
line through a label is a `FAIL`. An edge's own label is skipped, because it
sits on its own line by design. The fix in the message depends on the label: an
edge label can move along its line, and a shape or icon label needs the line
to go around it.

`SKILL.md` now says that a diagram is not done while the render did not run.
When draw.io writes no SVG, the skill asks the user to run the script outside
the sandbox.

**Side fix.** The label-fit check treated an edge-label cell as a shape of
0 px and warned about it. It now skips cells with a relative geometry.

## 2. One arrow per direction

**Problem.** An edge with an arrow head at both ends hides which side starts
the exchange. The user wants a second edge for data that flows back.

**Change.** The house style forbade nothing here and even suggested
`startArrow=block` for a two-way connection. That suggestion is gone. A new
rule asks for one edge per direction. The script reports an edge with a
`startArrow` and an end arrow as a `FAIL`.

**Checked by render.** The first version of the rule gave each edge one
waypoint, 15 px above or below the centre line. The render showed that draw.io
then bends each line back to the centre line before its target, and both labels
sat on those bends. With two waypoints per edge, one about 40 px from each
shape, each edge draws as one straight line, 30 px from the other. The script
then reports nothing. The rule now asks for two waypoints, and the waypoint
rule names this as an exception.

## 3. Notes grow when the text is edited

**Cause.** The house style asked for `autosize=1` on notes. draw.io's code
(`isAutoSizeCell`) resizes such a cell every time its label is edited.

**Change.** Notes get a fixed size that fits their text, with
`whiteSpace=wrap`, and no `autosize`. The script warns about a note with
`autosize=1`. The eval grader that required `autosize=1` now forbids it.

## 4. Icons in a group move when the group is resized

**Cause.** draw.io's code (`isRecursiveVertexResize`) scales and moves the
children of a shape when it is resized, unless the shape has
`recursiveResize=0`. draw.io's own group shapes, such as the AWS groups, set
`collapsible=0;recursiveResize=0;`.

**How it was settled.** The user's first answer pointed at selection: a click
selects the icon instead of the group. draw.io has `selectParentFirst=1` for
that. A test file with four groups (default, `recursiveResize=0`,
`selectParentFirst=1`, both) let the user try each in draw.io. The user chose
`recursiveResize=0` alone.

**Change.** Every group gets `recursiveResize=0`. The script warns about a
group without it. `references/style-keys.md` documents the key.

## 5. Found by the evals: the fan-out rule itself caused overlaps

**Problem.** The first eval round scored 1.00 on every grader, but a render of
the six diagrams outside the sandbox showed overlaps in all of them. The
graders are regexes and cannot see a route. The agents could not see one
either, because draw.io does not render inside the eval sandbox.

**Causes.**

- The rule "Several lines on one side" put every waypoint about 40 px from the
  shape. Each line then started at its own point, but all of them turned on
  the same row. Lines that turned the same way shared 46 to 130 px.
- A waypoint beyond the shape's corner, for example straight above a target
  further out, makes draw.io start from the middle of the top or bottom side
  again. Seven test renders showed this for every corner position.
- In the Azure case, lines left the App Service icon at the bottom, through its
  label.

**Changes.**

- The rule now nests the turns: the line nearest a corner turns 40 px out, the
  next 30 px further. The waypoint must stay within the side's span. Icons are
  connected on the left, right or top.
- `check_drawio.py` predicts these three cases from the file, without draw.io,
  so they show up inside a sandbox too. On the eval diagrams, its predicted
  overlap lengths matched the render exactly.
- A label box now ignores its outer 3 px. draw.io's box includes the extra line
  height, and a line along a cloud outline was reported for passing 3 px under
  a two-line label.

**Too slow to plan by hand.** With the corrected rules, the second Azure round
ran out of the 300 s limit in 2 of 3 runs. The agents spent 21,000 to 25,000
thinking tokens planning waypoints and wrote no file. The user chose a helper
script over a higher time limit.

**`scripts/spread_edges.py`.** Claude writes the edges without waypoints and
runs the helper. It gives each edge end that shares a side its own point along
the side and its own turn distance, and it keeps lines off the bottom of an
icon with a label. Choices that came out of testing:

- **Side per edge end.** A shape straight beside, above or below has one
  candidate side. A diagonal one has two, and joins the side that the straight
  neighbours of that shape use. A fixed preference for top and bottom broke a
  column of services; a choice by the larger gap broke a row.
- **Every end on a labelled icon gets a waypoint.** Without one, draw.io picks
  the side itself, and it picked the bottom.
- **Start points stay 10 px from the corners and at least 30 px apart.** On a
  small icon they may squeeze to 20 px before the helper asks for a larger
  shape. Asking earlier made it ask for nearly every icon.
- **`--edges`** limits the change to Claude's own edges in an existing file.

On the eight eval diagrams from rounds 1 to 3 that had failures, the helper
removed every overlap. One line still touched a cloud's label, which needs a
larger shape.

## Evals

- `gateway-fan-out-notes`: grader `04-notes-autosize` became
  `04-notes-no-autosize`, which fails on any note with `autosize=1`.
- `azure-group-long-labels`: new grader `05-one-arrow-head-per-edge` fails on
  an edge with a start arrow. Its webhook runs against a call, so the case
  tests the rule. New grader `06-group-keeps-icons-on-resize` fails on a
  group without `recursiveResize=0`.

The graders were tested against hand-made files: each matches the cell it
should, and nothing in a passing file.

## Eval results

Model `claude-sonnet-5`, judge `claude-haiku-4-5-20251001`, 3 runs per case.
The graders are regexes, so after each round every diagram was also checked
outside the sandbox with `check_drawio.py`, including the render. That column
is the one that matters for this change.

| Round | Skill state | Case | Graders | Diagrams clean in render |
| --- | --- | --- | --- | --- |
| 1 | new rules, old fan-out rule | gateway | 3/3 at 1.00 | 0 of 3 (lines on top of each other) |
| 1 | | azure | 3/3 at 1.00 | 0 of 3 (lines through an icon label) |
| 2 | nested turns, checks without render | gateway | 3/3 at 1.00 | 3 of 3 |
| 2 | | azure | 0.44 | 0 of 1; 2 runs timed out before writing |
| 3 | `spread_edges.py` | gateway | 3/3 at 1.00 | 3 of 3 |
| 3 | | azure | 3/3 at 1.00 | 2 of 3 |
| 4 | fewer turns, forced icon sides | azure | 0.94 | 0 of 3 (lines 9 to 10 px apart on small icons in two, a line through a label in one) |
| 5 | side capacity, two-pass placement | gateway | 3/3 at 1.00 | 3 of 3 |
| 5 | | azure | 3/3 at 1.00 | 2 of 3 |

"Clean" ignores a warning about a line to a note that probably crosses another
line; that warning appeared in one gateway diagram in rounds 3 and 5.

In round 5, the one Azure diagram with a finding had a 30 px overlap because
the agent moved an icon after running the helper and did not run it again.
Running the helper on the final file removes it. `SKILL.md` now says to run
the helper again after every move. That last sentence has not been through an
eval round.

The Azure case still hits its 300 s limit in 2 of 3 runs. The runs write a
passing file first and run out while checking or polishing. The case has no
`timeout_seconds`, while eight other cases in this suite set 600 s.

Total eval cost for this change: about $12.70.

## Considered and left out

**A default style per file.** A `.drawio` file cannot carry a default style.
draw.io's `getGraphXml` writes only page settings on `<mxGraphModel>` (grid,
page size, background), and "Set as Default Style" keeps the style in memory
only until the app closes. The lasting option is Extras > Configuration in
draw.io desktop ("Default Edge Style" and "Default Vertex Style", as JSON). It
applies to every diagram on the machine and needs a restart. The user chose
not to add this to the skill.

**The minimum gap between icons.** The gap stays 80 px between the outlines of
two shapes, measured from the icon picture, not from its label. The user chose
to keep it that way.
