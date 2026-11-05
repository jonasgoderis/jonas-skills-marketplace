# House style

These are the plugin author's style choices for draw.io diagrams. They are
preferences, not draw.io rules. To use your own style, change the values in this
file. `SKILL.md` reads its values from here, so nothing else needs to change.

## How to use this file

Use a decided value whenever you create the matching cell. For a value marked
TBD, leave the key out so draw.io uses its own default. Do not invent a value
for a TBD row. When you edit an existing file, follow that file's own choice for
a TBD row, so the diagram stays consistent.

## Values

| Setting | Key | House default | Why |
| --- | --- | --- | --- |
| Edge corners | `rounded` (on edges) | `0` | Sharp corners on edge bends. |
| Edge colour | `strokeColor` (on edges) | `#999999` | A grey line, so the shapes stand out more than the lines. See [Colour per flow](#colour-per-flow) for the one exception. |
| Edge width | `strokeWidth` (on edges) | `2` | The line width in pixels. |
| Arrow head | `endArrow` | `block` | A filled block marker at the end of an edge. draw.io's own default is `classic`. |
| Straight end | `targetJettySize` (on edges) | `30` | The line runs straight for at least 30 px before the arrow head, so the head never sits right on a bend. It overrides the automatic `jettySize` for the target end only. It works on edges without waypoints; see the waypoint rule for the others. |
| Edge labels | `labelBackgroundColor`, `defaultLabelBackgroundColor` (on edges with a label) | `default`, `page` | The line is cut out behind the label instead of running through it. |
| Edge label size | `fontSize` (on edges with a label and on edge label cells) | `12` | Edge labels stay readable. The `edgeLabel` class would set 11. |
| Icon labels | `labelBackgroundColor` (on icons) | `#FFFFFF` | A white box behind an icon's label, so a line under it does not cross the text. |
| Label wrapping | `whiteSpace`, `html` (on vertices) | `wrap`, `1` | Long labels wrap inside the shape instead of running over its border. |
| Icon label wrapping | `whiteSpace`, `html` (on icons) | `nowrap`, `1` | An icon's label sits under the picture. With `wrap`, it can only be as wide as the icon, often 64 px, and becomes a narrow stack of single words. |
| Icon label position | `verticalLabelPosition`, `verticalAlign`, `labelPosition`, `align` (on icons) | `bottom`, `top`, `center`, `center` | Every icon's label sits centred under the picture, never beside it or on top of it. Many style strings from draw.io's own libraries set no position, which puts the label on the picture, and a few put it to the right. Set these four keys on every icon, also when you copy a style string. |
| Note size | `width`, `height` (on the note's `mxGeometry`), `autosize` (on notes) | fit the text, `1` | Each note is as large as its own text needs, not as large as the other notes. `autosize=1` makes draw.io resize the note when someone edits its text. See [Labels](#labels). |
| Colour meanings | `fillColor`, `strokeColor` per kind of element | TBD | A fixed colour for each kind of thing, for example service or data store. |
| Vertex shape | `shape`, or a bare token such as `ellipse` | TBD | The default box shape. draw.io's own default is a rectangle. |
| Vertex corners | `rounded` (on vertices) | TBD | Sharp or rounded box corners. |
| Vertex fill | `fillColor` | TBD | The box background colour, as `#RRGGBB`. |
| Vertex border | `strokeColor` | TBD | The box border colour, as `#RRGGBB`. |
| Font family | `fontFamily` | TBD | The label font. draw.io's own default is Helvetica. |
| Font size | `fontSize` (on vertices) | TBD | The label size in pixels. draw.io's own default is 12. |
| Grid size | `gridSize` (attribute on `mxGraphModel`) | TBD | The snap grid in pixels. The reference examples use 10. |
| Page size | `pageWidth`, `pageHeight` (attributes on `mxGraphModel`) | TBD | The page in pixels. The reference examples use 850 × 1100. |

Grid size and page size are attributes on the `<mxGraphModel>` element. They are
not style keys, so they never go in a `style="…"` string.

The edge values above go after the rule B string in `SKILL.md`. With the current
values, a plain edge ends with
`strokeColor=#999999;strokeWidth=2;endArrow=block;targetJettySize=30;`,
and an edge with a label also gets
`labelBackgroundColor=default;defaultLabelBackgroundColor=page;fontSize=12;`.

## Colour per flow

Edges are grey by default. A diagram that shows several flows, such as a
request path and a data sync, may give each flow its own edge colour. This is
only allowed when the diagram has a legend that explains each colour. Without
the legend, a reader cannot know what a colour means. Keep the other edge
values (width, arrow head, jumps) the same for every flow. Name the colours in
your report, as a deliberate exception.

## Flat look

Do not set `shadow=1`, `sketch=1`, `comic=1`, `glass=1` or `gradientColor`. Set
`shadow="0"` on `<mxGraphModel>`. Avoid the colour theme classes such as `blue`
or `green` as bare tokens, because they add shadow, glass and a gradient.

## Spacing

Leave room between things. In a cramped diagram, a label can sit between
two lines, and the reader cannot see which line it belongs to.

- **Between shapes:** leave 80 to 120 px of empty space between the outlines of
  two shapes, both side by side and above each other. 80 px is the minimum.
  Choose the gap for each part of the diagram. A simple part, with few lines and
  short labels or none, reads best at about 80 px. Go towards 120 px where
  several lines meet one shape, where lines run side by side, or where lines
  carry labels. Too much space makes a small diagram large and empty. Too
  little space puts labels between lines.
- **Around a labelled edge:** the gap between the two shapes of an edge with a
  label is at least the label width plus 40 px on each side. Estimate the width
  as about 7 px per character at `fontSize=12`. A 10-character label then needs
  70 + 2 × 40 = 150 px. Use the larger of this and the 80 px minimum.
- **Between parallel lines:** two edges that run side by side stay at least
  30 px apart. If the routing puts them closer, move a shape or add waypoints
  (`<Array as="points">` in the edge geometry). Waypoints do not fix the
  attachment point, so they do not break rule A.
- **No line on top of another:** two lines must never run along the same
  stretch, because then one hides the other. Crossing is fine; the line jump
  shows it. Lines end up on top of each other in three common ways. Two edges
  between the same two shapes in opposite directions take exactly the same
  route: give each a waypoint so they run at least 30 px apart, or draw one
  edge with an arrow head at both ends (`startArrow=block`) when it means a
  two-way connection. Several edges on one side of a shape start at the same
  point: see the next item. Two edges between different shapes can pick the
  same corridor between two columns: move a shape, or add a waypoint to one of
  them. The script renders the diagram and reports every such stretch.
- **Several lines on one side:** when two or more edges leave or enter the
  same side of a shape, draw.io starts them all at the middle of that side.
  They then overlap and read as one line. Give each of these edges one
  waypoint, about 40 px outside the shape, at its own height within that
  side. For three edges on the right side, use 1/4, 1/2 and 3/4 of the shape's
  height. With a waypoint, draw.io's orthogonal router leaves the shape at the
  waypoint's height, so each line gets its own start point. For a top or bottom
  side, spread the `x` values in the same way. Order the waypoints like the
  targets, so the lines do not cross: the edge to the highest target leaves
  highest. Add `followTerminals=1` to these edges, so draw.io moves the
  waypoints along when someone drags the shape. Do not use `exitY` or `entryY`
  for this, because rule A forbids fixed points. One waypoint per edge is
  enough: draw.io still ends the line straight at the centre of its target.
- **Stacked lists:** items in a stack without edges between them, such as a
  column of queue boxes or a list of steps, may sit 10 to 20 px apart. The
  80 px minimum exists to leave room for lines and their labels. Without lines,
  the items read better as one group.
- **Label position:** keep an edge label on its line. It may move along the
  line: on an edge label cell, `mxGeometry x` runs from `-1` (the source end)
  to `1` (the target end), and `0` is the centre. Use that to move a label away
  from a crossing or a bend. Do not move it off the line: leave `mxGeometry y`
  at `0`, and do not add an `<mxPoint as="offset">` or `labelPlacement`. On its
  own line, with the line cut out behind it, the label cannot belong to
  anything else.
- **Waypoints:** put the last waypoint of an edge on the centre line of the
  target, on the axis where the edge enters it. Without a fixed entry point,
  draw.io aims at the centre of the target. A waypoint a few pixels off that
  line gives a small zigzag just before the arrow head. Keep the last waypoint
  at least 30 px from the target's outline. draw.io ignores `targetJettySize`
  on an edge with waypoints, so the waypoint itself must leave the straight end.
  The exception is several edges that enter the same side of the target: their
  last waypoints spread along that side, as described above.

## Layout

- **Centres in line:** two shapes joined by an edge, side by side, share the
  same centre `y` (`y + height / 2`). Two shapes above each other share the
  same centre `x`. Line up the centres, not the tops or the left edges. An icon
  of 64 px next to a box of 60 px with the same `y` is 2 px off, and draw.io
  then draws a small jog in a line that could be straight.
- **No crossings without need:** place the targets of a group of edges in the
  same order as their sources. If A1 sits above A2, the target of A1 sits above
  the target of A2. The same holds for several edges that leave one shape:
  order their targets the way the edges leave it. When two edges cross, first
  try to swap two shapes. Only keep a crossing when no swap removes it; the line
  jump then shows which line goes where.

These distances are minimums, apart from the stacked lists. Work them out from the `x`, `y`, `width` and
`height` of each `mxGeometry`. They are not style keys.

When you edit an existing file, apply the spacing to the shapes you add, and
move existing shapes only as far as you need to make room. If the existing
diagram is cramped, tell the user and offer to space it out.

## Labels

- **Length:** keep a label to at most 3 lines. Put longer text in a note: a
  separate text shape next to the thing it describes. Long labels are the most
  common cause of labels that overlap lines and other shapes.
- **Long labels on shapes and icons:** a label must stay inside its shape, and
  an icon label must stay narrow enough not to reach its neighbours. When a
  label is too long for one line, split it over 2 lines with `<br>` (the file
  uses `html=1`), at a word boundary near the middle, so both lines have about
  the same length. Use 3 lines only when 2 are not enough. Estimate the width
  as about 6 px per character at `fontSize=12`. In a box, each line must fit
  the box width minus 10 px, and the lines together must fit its height (about
  15 px per line, plus 10 px). An icon line stays under about 160 px, roughly
  25 characters. If 3 lines still do not fit, widen the shape, shorten the
  label, or move the detail into a note.
- **Note size:** size every note to its own text. Do not give all notes the
  same size: a short note in a large box leaves a block of empty space, and the
  diagram looks unfinished. Estimate the width as about 6 px per character of
  the longest line at `fontSize=12`, plus 20 px, and stop at about 300 px. Let
  longer lines wrap inside that width. Estimate the height as about 18 px per
  line, plus 20 px. Add `autosize=1`, so the note keeps fitting when someone
  edits its text in draw.io.
- **Numbered steps:** in a diagram that shows a flow in order, start each edge
  label with its step number: `1`, `2`, `3`. Steps that happen in parallel
  share a number with a letter: `6a`, `6b`. The reader can then follow the flow
  without guessing where it starts. A diagram without an order, such as a
  plain architecture overview, needs no numbers.

## Groups

Draw a group, such as a resource group, a network or a team boundary, as a real
container: a dashed rectangle with `container=1`, and the shapes inside it with
`parent="<group id>"`. The group may have a fill. Moving the group in draw.io
then moves everything in it. A plain rectangle drawn behind the shapes looks
the same, but leaves its contents behind when someone moves it.

draw.io draws a group together with everything in it, at the group's own place
in the file. That decides which lines show on top of a group's fill and which
lines its icons cover. The rules below follow from it.

- **Order:** within each parent, write the edges first, then the groups, then
  the other shapes and icons. Write a group before its children.
- **Coordinates:** a child's `x` and `y` are relative to the top-left corner of
  its group, not to the page. The waypoints of an edge are relative to the
  edge's own parent.
- **Edges:** an edge belongs to the parent of whichever of its two ends is drawn
  later. In practice:
  - Both ends in the same group: that group.
  - One end on the page and one in a group: the group.
  - Ends in two different groups: the group that comes later in the file.
  - Both ends on the page: the page, `parent="1"`.

  The line is then drawn after the fill of the group it enters, so the fill
  does not hide it. It is also drawn before the icons of that group, so it
  does not cover their labels. An edge on the page that enters a filled group
  disappears under the fill, and an edge after a group is drawn over its
  icons. Keep `source` and `target` on the shapes themselves, never on the
  group.
- **Lines between two groups:** the part of the line over the earlier group is
  drawn after all of that group, icons included. Route it so it does not pass
  over the earlier group's icons.
- **Lines that only pass over a group:** a line with no end inside a filled
  group disappears under its fill. Route it around the group with waypoints.
- **Editing in draw.io:** when someone reconnects an edge in the app, draw.io
  moves it to the closest parent that holds both ends, at the end of the file.
  It can then cover icons again. The script reports that.

## Icons above lines

An icon is a vertex drawn as a picture: `shape=image` or the bare `image`
token, or a stencil such as `shape=mxgraph.aws4.…`. Its text must sit above any
line that passes behind it.

draw.io has no z-index key. It draws the cells of one parent in the order they
appear in the XML, and a later cell lands on top. A group is drawn with all its
contents at the group's own place. So write every icon after all edges that
share its `parent`, and put each edge in the parent described under Groups.
Then every icon, also one inside a group, is drawn after the lines that reach
it. When you add an edge to an existing file, insert it before the icons, not
at the end. Together with the white label background from the table, the
icon's text then covers the line.

## File format

Save the file as plain, uncompressed XML, never with `compressed="true"`. Plain
XML gives readable diffs in git, and a later edit can read it directly.

draw.io keeps backup and draft files next to the diagram, named
`.$<file name>.bkp` and `.$<file name>.dtmp`. They should not be committed. In a
git repository without a rule for them, offer to add `.$*.bkp` and `.$*.dtmp` to
`.gitignore`.
