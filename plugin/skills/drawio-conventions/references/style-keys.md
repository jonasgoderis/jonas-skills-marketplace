# draw.io style keys

The keys this skill relies on, checked against the official
[draw.io style reference for AI diagram generation](https://www.drawio.com/docs/reference/diagram-generation/style-reference/).
That page is the authority. It also lists keys this file leaves out: sketch
style, images, behaviour flags, container layouts and style placeholders. Look
there before you use any key that is not in this file.

Descriptions here are short summaries. The spelling of every key and value is
copied exactly from the reference.

## Contents

- [Style string format](#style-string-format)
- [Edge routing](#edge-routing)
- [Connection points](#connection-points)
- [Arrow markers](#arrow-markers)
- [Fill and stroke](#fill-and-stroke)
- [Shape geometry](#shape-geometry)
- [Perimeters](#perimeters)
- [Text and labels](#text-and-labels)
- [mxGraphModel attributes](#mxgraphmodel-attributes)

## Style string format

- A style is a list of `key=value` pairs, each ending with `;`.
- Keys and values are case-sensitive. There are no spaces around `=` or `;`.
- Booleans are `0` and `1`, never `true` or `false`.
- Colours are `#RRGGBB`, `none` or `default`.
- A bare token without `=` sets a shape or a style class, for example `ellipse;` or `text;`.
- draw.io ignores unknown keys without an error.

## Edge routing

| Key | Values | draw.io default | What it does |
| --- | --- | --- | --- |
| `edgeStyle` | `orthogonalEdgeStyle`, `segmentEdgeStyle`, `elbowEdgeStyle`, `entityRelationEdgeStyle`, `isometricEdgeStyle`, `loopEdgeStyle`, `sideToSideEdgeStyle`, `topToBottomEdgeStyle`, `none` | — | The routing algorithm. `none` or empty draws a straight line. |
| `elbow` | `horizontal`, `vertical` | — | The direction of the bend for `elbowEdgeStyle`. |
| `rounded` | `0`, `1` | `1` on edges | Rounds the corners of an orthogonal edge. |
| `curved` | `0`, `1` | `0` | Draws the edge as a curve. |
| `curveGeometry` | `0`, `1` | `0` | With a curved edge: labels and line jumps follow the drawn curve. |
| `orthogonalLoop` | `0`, `1` | `1` | How an edge from a shape back to itself is routed. |
| `jettySize` | `auto`, a number | `auto` | The straight stub an orthogonal edge keeps before its first turn. |
| `sourceJettySize`, `targetJettySize` | number | — | The same stub, for one end only. |
| `jumpStyle` | `arc`, `gap`, `sharp`, `line` | — | How a crossing with another edge is drawn. |
| `jumpSize` | number | `6` | The width of the jump at a crossing. |
| `jumpLayers` | `0`, `1` | `1` | `0` limits jumps to crossings with edges on the same layer. |
| `libavoidRouting` | `0`, `1` | `0` | Routes an orthogonal edge around shapes in its way. |
| `followTerminals` | `0`, `1` | `0` | Waypoints move along when the connected shapes move. The house style sets it on edges whose waypoints spread several lines on one side of a shape. |

## Connection points

These keys pin an edge end to a fixed spot on a shape. The house style does not
set them unless the user asks. See rule A in `SKILL.md`.

| Key | Values | What it does |
| --- | --- | --- |
| `exitX`, `exitY` | `0.0`–`1.0` | Where the edge leaves the source, relative to its width and height. |
| `exitDx`, `exitDy` | number | A pixel offset added to the exit point. |
| `entryX`, `entryY` | `0.0`–`1.0` | Where the edge enters the target, relative to its width and height. |
| `entryDx`, `entryDy` | number | A pixel offset added to the entry point. |
| `exitPerimeter`, `entryPerimeter` | `0`, `1` | Whether a fixed point is projected onto the outline. Default `1`. |
| `portConstraint` | `eastwest`, `northsouth`, `perimeter`, `fixed` | Limits which sides an edge may use. |
| `sourcePerimeterSpacing`, `targetPerimeterSpacing` | number | A gap between the edge end and the shape. Default `0`. |

In the edge geometry, `<mxPoint as="sourcePoint">` and `<mxPoint as="targetPoint">`
give the ends of an edge with no `source` or `target`. A connected edge does not
need them.

## Arrow markers

| Key | Values | draw.io default | What it does |
| --- | --- | --- | --- |
| `startArrow` | arrow type | `none` | The marker at the start of the edge. |
| `endArrow` | arrow type | `classic` | The marker at the end of the edge. |
| `startSize`, `endSize` | number | — | The marker size. |
| `startFill`, `endFill` | `0`, `1` | `1` | `0` draws the marker as an outline only. |

Arrow types: `none`, `classic`, `classicThin`, `block`, `blockThin`, `open`,
`openThin`, `oval`, `diamond`, `diamondThin`, `box`, `halfCircle`, `circle`,
`circlePlus`, `cross`, `baseDash`, `doubleBlock`, `dash`, `async`, `openAsync`,
`manyOptional`.

## Fill and stroke

| Key | Values | draw.io default | What it does |
| --- | --- | --- | --- |
| `fillColor` | `#RRGGBB`, `none`, `default` | `default` | The shape background. |
| `strokeColor` | `#RRGGBB`, `none`, `default` | `default` | The border or line colour. |
| `strokeWidth` | number | `1` | The border or line width in pixels. |
| `dashed` | `0`, `1` | `0` | A dashed border or line. |
| `dashPattern` | string such as `8 8` | — | The dash and gap lengths. |
| `opacity` | `0`–`100` | `100` | The opacity of the whole cell. |
| `shadow` | `0`, `1` | `0` | A drop shadow. The house style keeps it off. |
| `gradientColor` | `#RRGGBB`, `none` | `none` | A gradient from `fillColor` to this colour. The house style does not use it. |
| `glass` | `0`, `1` | `0` | A shine effect on top of the shape. The house style keeps it off. |
| `sketch` | `0`, `1` | `0` | A hand-drawn look. The house style keeps it off. |
| `comic` | `0`, `1` | `0` | A comic-book look. The house style keeps it off. |

The colour theme classes (`blue`, `green`, `yellow`, `orange`, `red`, `pink`,
`purple`, `gray`, `turquoise`) are bare tokens that set a fill, a gradient, a
stroke, `shadow=1` and `glass=1` at once. The `plain-*` variants, such as
`plain-blue`, set the same colours without the shadow and the glass.

## Shape geometry

| Key | Values | draw.io default | What it does |
| --- | --- | --- | --- |
| `shape` | a shape name, for example `ellipse`, `rhombus`, `cylinder3`, `document` | `label` | The shape type. A rectangle needs no shape key. |
| `rounded` | `0`, `1` | `0` on vertices | Rounded corners. |
| `arcSize` | number | — | The corner size when `rounded=1`. |
| `aspect` | `variable`, `fixed` | `variable` | `fixed` keeps the width-to-height ratio. |
| `whiteSpace` | `wrap`, `nowrap` | — | `wrap` lets the label wrap inside the shape. |
| `container` | `0`, `1` | `0` | Makes the shape a container. Cells with `parent="<its id>"` sit inside it and move with it. |
| `html` | `0`, `1` | `1` | Allows HTML in the label. |

## Perimeters

A perimeter decides where an edge meets the outline. A non-rectangular shape
needs its matching perimeter, or edges end on its rectangular bounding box.

| `perimeter=` | Use with |
| --- | --- |
| `rectanglePerimeter` | rectangles (the default) |
| `ellipsePerimeter` | ellipses and circles |
| `rhombusPerimeter` | diamonds |
| `trianglePerimeter` | triangles |
| `hexagonPerimeter2` | hexagons |
| `parallelogramPerimeter` | parallelograms |
| `trapezoidPerimeter` | trapezoids |
| `calloutPerimeter` | callouts |
| `stepPerimeter` | step and chevron shapes |
| `cloudPerimeter` | clouds |

The bare tokens `ellipse`, `rhombus` and `triangle` set the shape and its
perimeter together.

## Icons and drawing order

An icon is a picture rather than a drawn outline. It is `shape=image` (or the
bare `image` token) with an `image=<url>`, or a stencil from a library, written
as `shape=mxgraph.<library>.<shape>`, for example the `mxgraph.aws4.*` icons.
A path such as `img/lib/azure2/app_services/Search_Services.svg` points to a
file inside draw.io itself. A wrong path renders as an empty box without any
error, so check it with `scripts/check_drawio.py`, and look names up with its
`--find` option. Where an icon's label sits is set by `verticalLabelPosition`
(`top`, `middle`, `bottom`) and `labelPosition` (`left`, `center`, `right`).
Without them, draw.io puts the label in the middle of the picture. A label
under the icon needs `verticalLabelPosition=bottom;verticalAlign=top;`, and the
house style adds `labelPosition=center;align=center;` to be explicit.

No style key sets the drawing order. draw.io draws the cells of one parent in
the order they appear in the XML, so a cell later in the file is drawn on top of
an earlier one.

## Text and labels

| Key | Values | draw.io default | What it does |
| --- | --- | --- | --- |
| `fontFamily` | font name | `Helvetica` | The label font. |
| `fontSize` | number | `12` | The label size in pixels. |
| `fontColor` | `#RRGGBB`, `default` | `default` | The label colour. |
| `fontStyle` | bitmask | `0` | `1` bold, `2` italic, `4` underline. Add them up to combine. |
| `align` | `left`, `center`, `right` | `center` | Horizontal text alignment. |
| `verticalAlign` | `top`, `middle`, `bottom` | `middle` | Vertical text alignment. |
| `verticalLabelPosition` | `top`, `middle`, `bottom` | `middle` | Puts the whole label above, on or below the shape. |
| `labelPosition` | `left`, `center`, `right` | `center` | Puts the whole label left of, on or right of the shape. |
| `autosize` | `0`, `1` | `0` | draw.io resizes the shape to fit its label whenever someone edits the label. It does not resize when the file is opened, so set a fitting size as well. |
| `labelBackgroundColor` | `#RRGGBB`, `none`, `default` | — | A background behind the label, useful on edges. |
| `defaultLabelBackgroundColor` | `page` | — | With `labelBackgroundColor=default`: no background box. The label is cut out of the edge instead. |

## mxGraphModel attributes

These are attributes on the `<mxGraphModel>` element, not style keys.

| Attribute | Value in the reference examples | What it does |
| --- | --- | --- |
| `grid` | `1` | Shows the grid. |
| `gridSize` | `10` | The grid step in pixels. |
| `page` | `1` | Shows the page outline. |
| `pageWidth` | `850` | The page width in pixels. |
| `pageHeight` | `1100` | The page height in pixels. |
| `pageScale` | `1` | The page scale. |
| `shadow` | `0` | Shadows for the whole diagram. The house style sets `0`. |

A draw.io file can also be saved with `compressed="true"`. The reference says
generated files should not use it, and the house style never does.
