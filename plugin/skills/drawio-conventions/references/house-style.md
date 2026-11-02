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
| Edge colour | `strokeColor` (on edges) | `#999999` | A grey line, so the shapes stand out more than the lines. |
| Edge width | `strokeWidth` (on edges) | `2` | The line width in pixels. |
| Arrow head | `endArrow` | `block` | A filled block marker at the end of an edge. draw.io's own default is `classic`. |
| Edge labels | `labelBackgroundColor`, `defaultLabelBackgroundColor` (on edges with a label) | `default`, `page` | The line is cut out behind the label instead of running through it. |
| Edge label size | `fontSize` (on edges with a label and on edge label cells) | `12` | Edge labels stay readable. The `edgeLabel` class would set 11. |
| Icon labels | `labelBackgroundColor` (on icons) | `#FFFFFF` | A white box behind an icon's label, so a line under it does not cross the text. |
| Label wrapping | `whiteSpace`, `html` (on vertices) | `wrap`, `1` | Long labels wrap inside the shape instead of running over its border. |
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
values, a plain edge ends with `strokeColor=#999999;strokeWidth=2;endArrow=block;`,
and an edge with a label also gets
`labelBackgroundColor=default;defaultLabelBackgroundColor=page;fontSize=12;`.

## Flat look

Do not set `shadow=1`, `sketch=1`, `comic=1`, `glass=1` or `gradientColor`. Set
`shadow="0"` on `<mxGraphModel>`. Avoid the colour theme classes such as `blue`
or `green` as bare tokens, because they add shadow, glass and a gradient.

## Spacing

Leave room between things. In a cramped diagram, a label can sit between
two lines, and the reader cannot see which line it belongs to.

- **Between shapes:** at least 80 px of empty space between the outlines of two
  shapes, both side by side and above each other.
- **Around a labelled edge:** the gap between the two shapes of an edge with a
  label is at least the label width plus 40 px on each side. Estimate the width
  as about 7 px per character at `fontSize=12`. A 10-character label then needs
  70 + 2 × 40 = 150 px.
- **Between parallel lines:** two edges that run side by side stay at least
  30 px apart. If the routing puts them closer, move a shape or add waypoints
  (`<Array as="points">` in the edge geometry). Waypoints do not fix the
  attachment point, so they do not break rule A.
- **Label position:** leave an edge label on its line, centred. Do not move it
  with an offset or with `labelPlacement`. On its own line, with the line cut out
  behind it, the label cannot belong to anything else.

These distances are minimums. Work them out from the `x`, `y`, `width` and
`height` of each `mxGeometry`. They are not style keys.

When you edit an existing file, apply the spacing to the shapes you add, and
move existing shapes only as far as you need to make room. If the existing
diagram is cramped, tell the user and offer to space it out.

## Icons above lines

An icon is a vertex drawn as a picture: `shape=image` or the bare `image`
token, or a stencil such as `shape=mxgraph.aws4.…`. Its text must sit above any
line that passes behind it.

draw.io has no z-index key. It draws the cells of one parent in the order they
appear in the XML, and a later cell lands on top. So write every icon after all
edges that share its `parent`. When you add an edge to an existing file, insert
it before the icons, not at the end. Together with the white label background
from the table, the icon's text then covers the line.

## File format

Save the file as plain, uncompressed XML, never with `compressed="true"`. Plain
XML gives readable diffs in git, and a later edit can read it directly.
