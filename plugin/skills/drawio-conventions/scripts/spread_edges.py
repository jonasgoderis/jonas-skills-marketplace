#!/usr/bin/env python3
"""Give edges that share a side of a shape their own waypoints.

Usage: spread_edges.py <file.drawio> [--edges ID,ID] [--write]

draw.io starts every edge on one side of a shape at the middle of that side,
so the lines run on top of each other. This script works out one waypoint per
edge end that shares a side, following the "Several lines on one side" and
"One direction per edge" rules in references/house-style.md:

- each edge gets its own point along the side, in the order of the shapes at
  the other ends, so the lines do not cross;
- each edge turns at its own distance from the shape: the edge nearest a
  corner turns 40 px out, the next one 30 px further, so lines that turn the
  same way do not share a stretch;
- an edge never uses the bottom side of an icon with a label, because the
  label sits there; it moves to the left or right side instead.

It replaces the waypoints of the edges it changes and adds followTerminals=1.
Without --write it only prints what it would change. With --edges it changes
only those edges, which is what you want in a file someone else also edits.
Edges with fixed connection points are left alone.

Run check_drawio.py afterwards. This script only handles shared sides; lines
that pick the same corridor between other shapes still need a look.
"""

import argparse
import sys
import xml.etree.ElementTree as ET

FIRST_TURN = 40   # distance from the shape of the first turn
TURN_STEP = 30    # extra distance for each next turn on the same side
LAST_STRAIGHT = 30  # straight end before the shape at the other end
MIN_APART = 30    # parallel lines stay at least this far apart
CORNER_MARGIN = 10  # keep start points this far from the corners
MIN_SQUEEZED = 20   # on a small shape, accept points this close before asking for more room
FIXED_POINT_KEYS = ("exitX", "exitY", "entryX", "entryY")


def parse_style(style):
    keys, tokens = {}, set()
    for part in (style or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            keys[k] = v
        elif part:
            tokens.add(part)
    return tokens, keys


def cell_of(el):
    return el if el.tag == "mxCell" else el.find("mxCell")


def is_icon(tokens, keys):
    shape = keys.get("shape", "")
    return "image" in tokens or shape == "image" or shape.startswith("mxgraph.")


def spread(model, only, notes):
    root = model.find("root")
    cells, parent = {}, {}
    for el in root:
        c = cell_of(el)
        if c is not None and el.get("id"):
            cells[el.get("id")] = (el, c)
            parent[el.get("id")] = c.get("parent")

    def origin(cid):
        """Absolute top-left corner of a cell's coordinate frame."""
        x = y = 0.0
        seen = set()
        while cid in cells and cid not in seen:
            seen.add(cid)
            g = cells[cid][1].find("mxGeometry")
            if cells[cid][1].get("vertex") == "1" and g is not None and g.get("relative") != "1":
                x += float(g.get("x", 0))
                y += float(g.get("y", 0))
            cid = parent.get(cid)
        return x, y

    def box(cid):
        g = cells[cid][1].find("mxGeometry")
        if g is None or g.get("relative") == "1":
            return None
        ox, oy = origin(parent.get(cid))
        return (ox + float(g.get("x", 0)), oy + float(g.get("y", 0)),
                float(g.get("width", 0)), float(g.get("height", 0)))

    def labelled_icon(cid):
        c = cells[cid][1]
        tokens, keys = parse_style(c.get("style"))
        return (is_icon(tokens, keys) and c.get("value")
                and keys.get("verticalLabelPosition") == "bottom")

    edges = []
    for cid, (el, c) in cells.items():
        if c.get("edge") != "1" or (only and cid not in only):
            continue
        src, tgt = c.get("source"), c.get("target")
        if src not in cells or tgt not in cells:
            continue
        _, keys = parse_style(c.get("style"))
        if any(k in keys for k in FIXED_POINT_KEYS):
            notes.append(f"{cid}: has a fixed connection point; left alone")
            continue
        a, b = box(src), box(tgt)
        if a and b:
            edges.append((cid, src, tgt, a, b))

    def centre(r):
        return r[0] + r[2] / 2, r[1] + r[3] / 2

    def candidates(me, other):
        """The sides of `me` that face `other`. One side when the other shape
        lies straight beside, above or below; two when it lies diagonally."""
        (cx, cy), (ox, oy) = centre(me), centre(other)
        gap_x = max(other[0] - (me[0] + me[2]), me[0] - (other[0] + other[2]))
        gap_y = max(other[1] - (me[1] + me[3]), me[1] - (other[1] + other[3]))
        h = "right" if ox > cx else "left"
        v = "bottom" if oy > cy else "top"
        if gap_x > 0 and gap_y > 0:
            return [h, v] if gap_x >= gap_y else [v, h]
        return [h] if gap_x > gap_y else [v]

    # Pass 1: every end gets its candidate sides. Pass 2: a diagonal end
    # joins the candidate side that most straight ends of that shape use, so
    # a row of targets below, or a column beside, shares one side.
    ends = []  # [edge id, which end, shape id, other box, candidates]
    for cid, src, tgt, a, b in edges:
        ends.append([cid, "source", src, b, candidates(a, b)])
        ends.append([cid, "target", tgt, a, candidates(b, a)])
    straight = {}
    for cid, end, shape_id, other, cands in ends:
        if len(cands) == 1:
            straight[(shape_id, cands[0])] = straight.get((shape_id, cands[0]), 0) + 1

    sides = {}  # (shape, side) -> [(edge id, which end, the other shape's box)]
    moved = []  # ends moved off the bottom of an icon, placed last
    for cid, end, shape_id, other, cands in ends:
        side = max(cands, key=lambda c: (straight.get((shape_id, c), 0), -cands.index(c)))
        if side == "bottom" and labelled_icon(shape_id):
            moved.append((cid, end, shape_id, other))
            continue
        sides.setdefault((shape_id, side), []).append((cid, end, other))
    # An icon's label sits under it, so its bottom side is not used. Such an
    # end goes to the emptier of the left and right sides.
    forced = set()
    for cid, end, shape_id, other in moved:
        me = box(shape_id)
        towards = "right" if centre(other)[0] >= centre(me)[0] else "left"
        away = "left" if towards == "right" else "right"
        side = min((towards, away), key=lambda c: (len(sides.get((shape_id, c), [])), c != towards))
        sides.setdefault((shape_id, side), []).append((cid, end, other))
        forced.add((shape_id, side))

    # A side holds as many lines as fit MIN_SQUEEZED apart inside its corners.
    # Move the extra lines of a full side to a free side of the same shape,
    # the one that faces their other end most. A small icon has room for one
    # or two lines per side, so this spreads its lines over left, right and top.
    def capacity(me, side):
        length = me[2] if side in ("top", "bottom") else me[3]
        return max(1, int((length - 2 * CORNER_MARGIN) // MIN_SQUEEZED) + 1)

    def facing_score(me, other, side):
        (cx, cy), (ox, oy) = centre(me), centre(other)
        return {"right": ox - cx, "left": cx - ox, "bottom": oy - cy, "top": cy - oy}[side]

    for shape_id in {k[0] for k in sides}:
        me = box(shape_id)
        allowed = ["top", "left", "right"] + ([] if labelled_icon(shape_id) else ["bottom"])
        for _ in range(20):
            full = [s for s in allowed + ["bottom"]
                    if len(sides.get((shape_id, s), [])) > capacity(me, s)]
            if not full:
                break
            best = None
            for s in full:
                for item in sides[(shape_id, s)]:
                    for alt in allowed:
                        if alt == s or len(sides.get((shape_id, alt), [])) >= capacity(me, alt):
                            continue
                        score = facing_score(me, item[2], alt)
                        if best is None or score > best[0]:
                            best = (score, s, item, alt)
            if best is None:
                break  # every side is full; the squeeze note below says so
            _, s, item, alt = best
            sides[(shape_id, s)].remove(item)
            sides.setdefault((shape_id, alt), []).append(item)
            forced.add((shape_id, alt))

    def spread_side(shape_id, side, items, aim):
        """Order the ends on one side by where they head (`aim`), and give
        each its point along the side. Returns [(item, spot)]."""
        me = box(shape_id)
        horizontal = side in ("top", "bottom")  # positions run along x
        axis = 0 if horizontal else 1
        start, length = (me[0], me[2]) if horizontal else (me[1], me[3])
        items = sorted(items, key=lambda it: (aim(it)[axis], it[0]))
        n = len(items)
        # Spread evenly, but keep the lines at least 30 px apart, centred on
        # the side. If that does not fit, squeeze them inside the corners: a
        # point on or beyond a corner makes draw.io leave from another side.
        step = max(length / (n + 1), MIN_APART)
        room = length - 2 * CORNER_MARGIN
        if n > 1 and step * (n - 1) > room:
            step = room / (n - 1)
        first = start + length / 2 - step * (n - 1) / 2
        return [(it, first + i * step) for i, it in enumerate(items)], step

    def on_side(me, side, spot):
        return {"bottom": (spot, me[1] + me[3]), "top": (spot, me[1]),
                "right": (me[0] + me[2], spot), "left": (me[0], spot)}[side]

    used = {k: v for k, v in sides.items()
            if len(v) >= 2 or k in forced or labelled_icon(k[0])}
    # On an icon with a label, every end gets a waypoint. Without one, draw.io
    # picks the side itself, and it may pick the bottom.

    # Pass 1: where each end meets its shape, aiming at the other shape.
    meet = {}
    for (shape_id, side), items in used.items():
        placed, _ = spread_side(shape_id, side, items, lambda it: centre(it[2]))
        for (cid, end, other), spot in placed:
            meet[(cid, end)] = on_side(box(shape_id), side, spot)

    # Pass 2: order and turn by where the other end really meets its shape,
    # which may be a different side than its centre suggests.
    def aim_of(it):
        cid, end, other = it
        return meet.get((cid, "target" if end == "source" else "source"), centre(other))

    points = {}  # (edge id, end) -> absolute waypoint
    for (shape_id, side), items in used.items():
        me = box(shape_id)
        axis = 0 if side in ("top", "bottom") else 1
        placed, step = spread_side(shape_id, side, items, aim_of)
        if len(placed) > 1 and step < MIN_SQUEEZED:
            notes.append(f"{shape_id}: {len(placed)} lines on its {side} side end up only {step:.0f} px apart; make the shape larger, or connect a line to another side")
        # Nest the turns: per direction, the edge nearest the corner it turns
        # towards gets the first distance.
        turn = {}
        for sign in (-1, 1):
            group = [(i, spot) for i, (it, spot) in enumerate(placed)
                     if (aim_of(it)[axis] - spot) * sign > 0]
            group.sort(key=lambda g: g[1] * sign, reverse=True)
            for k, (i, _) in enumerate(group):
                turn[i] = FIRST_TURN + k * TURN_STEP
        for i, ((cid, end, other), spot) in enumerate(placed):
            dist = turn.get(i, FIRST_TURN)
            # Room before the shape at the other end, on this side's axis.
            room = {"bottom": other[1] - (me[1] + me[3]), "top": me[1] - (other[1] + other[3]),
                    "right": other[0] - (me[0] + me[2]), "left": me[0] - (other[0] + other[2])}[side]
            if room > 0 and dist > room - LAST_STRAIGHT:
                notes.append(f"{cid}: needs a turn {dist} px from {shape_id} on its {side} side, but the gap is {room:.0f} px; widen the gap to about {dist + LAST_STRAIGHT} px")
            points[(cid, end)] = {"bottom": (spot, me[1] + me[3] + dist), "top": (spot, me[1] - dist),
                                  "right": (me[0] + me[2] + dist, spot), "left": (me[0] - dist, spot)}[side]

    changed = []
    for cid, src, tgt, a, b in edges:
        wps = [points[(cid, e)] for e in ("source", "target") if (cid, e) in points]
        if not wps:
            continue
        el, c = cells[cid]
        ox, oy = origin(c.get("parent"))
        g = c.find("mxGeometry")
        if g is None:
            g = ET.SubElement(c, "mxGeometry", {"relative": "1", "as": "geometry"})
        for old in g.findall("Array"):
            g.remove(old)
        arr = ET.SubElement(g, "Array", {"as": "points"})
        for x, y in wps:
            ET.SubElement(arr, "mxPoint", {"x": f"{x - ox:g}", "y": f"{y - oy:g}"})
        style = c.get("style") or ""
        if "followTerminals=1" not in style:
            c.set("style", (style if style.endswith(";") or not style else style + ";") + "followTerminals=1;")
        changed.append((cid, [(round(x - ox), round(y - oy)) for x, y in wps]))
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--edges", help="comma-separated edge ids to change; default: every edge")
    ap.add_argument("--write", action="store_true", help="write the file; without it, only report")
    args = ap.parse_args()
    only = {e.strip() for e in args.edges.split(",")} if args.edges else None

    tree = ET.parse(args.file)
    top = tree.getroot()
    models = [top] if top.tag == "mxGraphModel" else []
    for d in top.findall("diagram"):
        m = d.find("mxGraphModel")
        if m is None:
            sys.exit(f"tab '{d.get('name')}' is compressed; save it as plain XML first")
        models.append(m)

    total = 0
    for i, model in enumerate(models):
        name = top.findall("diagram")[i].get("name") if top.tag == "mxfile" else "(single)"
        notes = []
        changed = spread(model, only, notes)
        for cid, wps in changed:
            print(f"[{name}] {cid}: waypoints {wps}")
        for n in notes:
            print(f"[{name}] NOTE {n}")
        total += len(changed)
    if args.write and total:
        tree.write(args.file, encoding="utf-8", xml_declaration=False)
        print(f"Wrote {total} edge(s). Run check_drawio.py next.")
    elif total:
        print(f"{total} edge(s) would change. Add --write to save.")
    else:
        print("No shared sides found; nothing to change.")


if __name__ == "__main__":
    main()
