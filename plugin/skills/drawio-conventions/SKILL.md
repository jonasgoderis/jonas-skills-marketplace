---
name: drawio-conventions
description: House style for draw.io diagrams — how edges attach to shapes, line jumps on by default, a configurable set of default style values, and a checklist to run before a diagram is called done. Use it any time a .drawio file or draw.io XML (mxfile, mxGraphModel, mxCell) is created, edited, regenerated or fixed, including when another skill or a script writes the XML. Reach for it when the user asks for a "diagram in draw.io", mentions "drawio", "draw.io" or "diagrams.net", asks to add a box or an arrow to an existing .drawio file, or says the arrows stay stuck after moving a shape. This skill sets conventions and bundles a script that checks the finished file. It does not teach the XML format and does not export diagrams to images for the user, so use it alongside the skill that does the drawing.
---

# draw.io conventions

This skill is a conventions layer. Another skill or your own knowledge writes the draw.io XML. This skill decides how that XML must look. Where a drawing skill or a generator script says something different, the rules here win. If a script writes fixed connection points, remove them from its output before you run the checklist in section E.

The skill has four parts:

- Rules A and B below are general. They keep a diagram editable, whoever's style it uses.
- `references/house-style.md` holds the style values: colours, arrow type, label sizes, icon rules. Read it every time this skill fires. The values there are personal choices and may be replaced.
- `references/style-keys.md` lists the draw.io style keys that matter here. Read it before you use a key you are not sure of. draw.io ignores unknown keys without any error, so a wrong key fails silently.
- `scripts/check_drawio.py` runs the mechanical part of the checklist in section E over the file on disk.

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

Apply everything in `references/house-style.md`: the values table, the colour per flow, the spacing, the labels, the groups, the flat look, the icon rules and the file format. That file also says what to do with a value marked TBD: leave the key out, so draw.io uses its own default.

If `references/house-style.md` is missing, apply rules A and B only. Leave every other key at draw.io's default.

## D. Write the file without losing anyone's work

A `.drawio` file is often edited by two parties: you, and the user in the draw.io app. Each step below stops one of them from silently overwriting the other.

**A generator script exists.** Sometimes a script builds the diagram, and you change the diagram by changing the script. The user may have opened the file in draw.io since the last run, and moved or added shapes. A new run would delete that work without any warning. So before you run the script again, compare the file on disk with what the script produces now. If they differ in ways the script did not cause, those are the user's edits. Copy them into the script first, or ask the user. Never run the script over them.

**The file has unsaved changes in draw.io.** The draw.io desktop app keeps a draft of unsaved changes next to the file, as `.$<file name>.dtmp`, for example `.$flow.drawio.dtmp`. If that draft exists, the file is probably open with unsaved work, or draw.io crashed with work in it. Tell the user before you write. Ask them to save or close the diagram first, or to reload it after your change. Otherwise draw.io can save its open copy over your new file. A `.$<file name>.bkp` file is different: draw.io writes it on every save and keeps it, so it does not mean the file is open. It does hold the previous version, which helps when something was overwritten.

**The file has several tabs.** Each `<diagram>` element is one tab (page). Give every `<diagram>` a unique `id` and a unique `name`, and keep the existing tab order. Add a new tab as the last `<diagram>`, just before `</mxfile>`. Cell ids only need to be unique within one tab.

**Read the file back.** After you write, check the file on disk, not your copy in memory. An editor, a sync tool or an open draw.io window can put a different version there. The checklist in section E does this, because the script parses the file from disk.

## E. Check before you say it is done

Run the script over the file on disk first:

```bash
python3 <skill dir>/scripts/check_drawio.py <file.drawio> [--expect-tabs "Tab one,Tab two"]
```

It reports every cell in the file, so in an existing file it also reports untouched cells. Fix the findings on your own cells, and report the rest to the user. A `FAIL` breaks a rule. A `WARN` needs a look, because it may be a deliberate exception, such as a fixed point the user asked for. The warnings also point out layout problems: two shapes closer than 80 px, two connected shapes whose centres do not line up, two edges that probably cross without need, several lines that start or end at the same point of a shape, labels too long for their shape or too wide under an icon, and notes much larger than their text. Fix those on your own cells. An icon whose label is not under the picture is a `FAIL`. So is an edge drawn after an icon it can pass over, also when the icon sits inside a group that comes before the edge. An edge with an end inside a group belongs inside that group; outside it, the line disappears under a filled group, which is a `FAIL`.

When draw.io desktop is installed, the script also renders each tab to SVG with it, and reads the routes draw.io really draws. Two lines that run on top of each other are a `FAIL`, because one hides the other. Two lines closer than 12 px are a `WARN`. Rendering takes a few seconds per tab. Use `--no-render` only when draw.io hangs, and then say in your report that overlapping lines were not checked.

The script also checks icon names against the installed draw.io app. A wrong image path (`image=img/lib/...`) renders as an empty box without any error, so it is a `FAIL`. Stencil names (`shape=mxgraph....`) get a `WARN` when the script does not know them, because its list of stencils is not complete. If draw.io is not installed, the script says the names were not checked, so say that in your report.

To find the right icon before you write it, run the script with `--find`, for example `--find "api gateway"` or `--find search`. In one call it lists the matching image paths and stencil names. For most stencils it also prints a full style string from draw.io's own code. Copy that string, then add the icon values from `references/house-style.md`, such as the white label background, `whiteSpace=nowrap` and the label position under the icon. Many of draw.io's own strings put the label on the picture or beside it, so replace those keys. Look up all the icons you need in one call, for example `--find "api gateway" lambda rds users`, because each separate call costs a turn.

Do not search the draw.io app files by hand, with `find`, `strings` or by unpacking the archive. The script already reads those files. In test runs, a manual search used up every available turn before the diagram was written. If `--find` finds nothing, use the name you know from the draw.io sidebar, and mention it in your report.

The script does not know the house-style values, because a user can replace them. Check those by hand with the list below.

The list covers the cells you added or changed. In an existing file, an untouched cell that fails an item is reported to the user, not fixed. Fix every failure in your own cells, then run the script and the list again. Items marked *(script)* are covered by the script.

1. *(script)* Every edge (`edge="1"`) has a `source` and a `target`, and both ids exist in the file.
2. *(script)* No edge style contains `exitX`, `exitY`, `entryX`, `entryY`, `exitDx`, `exitDy`, `entryDx` or `entryDy`, unless the user asked for that fixed point.
3. *(script)* No edge with both a `source` and a `target` has a `sourcePoint` or `targetPoint`.
4. *(script)* Every edge style contains `edgeStyle=orthogonalEdgeStyle`, `jumpStyle=arc` and `jumpSize=6`.
5. Every edge, edge label cell, vertex and icon carries the decided values from `references/house-style.md` that apply to it.
6. *(script)* Every non-rectangular shape has the matching `perimeter`.
7. Nothing breaks the spacing, the label rules, the flat look, the icon order, the groups or the file format in `references/house-style.md`. The script covers the flat look, the drawing order of icons and groups, the icon label position, the label lengths, the file format, the note sizes, lines on top of each other, and the spacing, alignment, crossings and shared start points of shapes joined by an edge. Compare the rest by hand, using the `mxGeometry` of neighbouring shapes. Within the 80 to 120 px range, check that busy parts got the wider gaps.
8. Every style key you used appears in `references/style-keys.md` or in the official reference, and no TBD value was invented.

In your report, say that the script and the checklist passed. Name any deliberate exception, such as a fixed point the user asked for, or a colour per flow. List any untouched edges that break rule A, and offer to fix them.
