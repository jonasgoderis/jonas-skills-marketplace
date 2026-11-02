---
name: drawio-conventions
description: House style for draw.io diagrams — how edges attach to shapes, line jumps on by default, a configurable set of default style values, and a checklist to run before a diagram is called done. Use it any time a .drawio file or draw.io XML (mxfile, mxGraphModel, mxCell) is created, edited, regenerated or fixed, including when another skill or a script writes the XML. Reach for it when the user asks for a "diagram in draw.io", mentions "drawio", "draw.io" or "diagrams.net", asks to add a box or an arrow to an existing .drawio file, or says the arrows stay stuck after moving a shape. This skill only sets conventions. It does not teach the XML format and does not render or validate diagrams, so use it alongside the skill that does the drawing.
---

# draw.io conventions

This skill is a conventions layer. Another skill or your own knowledge writes the draw.io XML. This skill decides how that XML must look. Where a drawing skill or a generator script says something different, the rules here win. If a script writes fixed connection points, remove them from its output before you run the checklist in section D.

The skill has three parts:

- Rules A and B below are general. They keep a diagram editable, whoever's style it uses.
- `references/house-style.md` holds the style values: colours, arrow type, label sizes, icon rules. Read it every time this skill fires. The values there are personal choices and may be replaced.
- `references/style-keys.md` lists the draw.io style keys that matter here. Read it before you use a key you are not sure of. draw.io ignores unknown keys without any error, so a wrong key fails silently.

Apply these rules to every edge and shape you add or change. When you edit an existing file, leave untouched cells as they are, even when they break a rule here. The user may have pinned an old edge on purpose, and a change they did not ask for is hard to spot in a diagram. Instead, tell the user which edges break rule A, and offer to fix them.

## A. Edges connect to the shape, not to a fixed point

Give every edge `source="<cell id>"` and `target="<cell id>"`. Leave the attachment point to draw.io.

Do not set these keys unless the user asks for a fixed connection point: `exitX`, `exitY`, `entryX`, `entryY`, `exitDx`, `exitDy`, `entryDx`, `entryDy`.

Do not add `<mxPoint as="sourcePoint">` or `<mxPoint as="targetPoint">` to an edge that connects two shapes. Those points are only for an edge with a loose end.

The reason: without a fixed point, draw.io works out where the edge meets the shape's outline (its perimeter). When someone moves a shape later, draw.io recalculates that point, and the edge stays clean. A fixed point stays on the same spot of the shape. After a move, the edge then bends around the shape or leaves from the wrong side.

This works best when non-rectangular shapes have the matching `perimeter`, for example `rhombus` with `perimeter=rhombusPerimeter`. Without it, the edge ends on the invisible bounding box.

Good — the edge names both shapes and nothing else (house-style values left out for brevity):

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;jumpStyle=arc;jumpSize=6;"
        edge="1" parent="1" source="api" target="db">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

Bad — fixed exit and entry points, plus loose end points on a connected edge:

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;html=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
        edge="1" parent="1" source="api" target="db">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="240" y="130" as="sourcePoint" />
    <mxPoint x="400" y="130" as="targetPoint" />
  </mxGeometry>
</mxCell>
```

When the user does ask for a fixed point, set only the keys for that end of that edge. Mention it in your report, so the exception is visible.

## B. Line jumps are on by default

Start every edge from this style string:

```
edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;jumpStyle=arc;jumpSize=6;
```

A line jump (a small arc where two edges cross) shows clearly which line goes where. `edgeStyle=orthogonalEdgeStyle` is part of the default because jumps sit on straight horizontal and vertical segments; a curved edge only gets jumps with `curveGeometry=1`.

Then append the edge values from `references/house-style.md`. Add other keys after that. Do not remove keys unless the user asks.

## C. House style

Apply everything in `references/house-style.md`: the values table, the spacing, the flat look, the icon rules and the file format. That file also says what to do with a value marked TBD: leave the key out, so draw.io uses its own default.

If `references/house-style.md` is missing, apply rules A and B only. Leave every other key at draw.io's default.

## D. Check before you say it is done

Run this over the final XML, not over your memory of what you wrote. Search the file text for each item. The list covers the cells you added or changed. In an existing file, an untouched cell that fails an item is reported to the user, not fixed. Fix every failure in your own cells, then run the list again.

1. Every edge (`edge="1"`) has a `source` and a `target`, and both ids exist in the file.
2. No edge style contains `exitX`, `exitY`, `entryX`, `entryY`, `exitDx`, `exitDy`, `entryDx` or `entryDy`, unless the user asked for that fixed point.
3. No edge with both a `source` and a `target` has a `sourcePoint` or `targetPoint`.
4. Every edge style contains `edgeStyle=orthogonalEdgeStyle`, `jumpStyle=arc` and `jumpSize=6`.
5. Every edge, edge label cell, vertex and icon carries the decided values from `references/house-style.md` that apply to it.
6. Every non-rectangular shape has the matching `perimeter`.
7. Nothing breaks the spacing, the flat look, the icon order or the file format in `references/house-style.md`. For spacing, compare the `mxGeometry` of neighbouring shapes.
8. Every style key you used appears in `references/style-keys.md` or in the official reference, and no TBD value was invented.

In your report, say that the checklist passed. Name any deliberate exception, such as a fixed point the user asked for. List any untouched edges that break rule A, and offer to fix them.
