#!/usr/bin/env python3
"""Run the mechanical part of the drawio-conventions checklist over a file.

Usage: check_drawio.py <file.drawio> [--drawio-asar PATH] [--expect-tabs NAME,NAME]
       check_drawio.py --find TERM [TERM ...]   list draw.io icon paths and stencil names per TERM

It reads the file from disk, so it checks what was really written, not what
the caller meant to write. It covers the general rules (A and B, flat look,
drawing order, file format, tabs, layout of connected shapes, icon names). It does not
know the house-style values, because a user can replace them: compare those by
hand against references/house-style.md.

Output: one line per finding, FAIL or WARN, with the tab name and cell id.
A FAIL breaks a rule. A WARN needs a human look: it may be a deliberate
exception, such as a fixed point the user asked for. Exit code 1 on any FAIL.
"""

import argparse
import base64
import json
import os
import re
import struct
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

FIXED_POINT_KEYS = ("exitX", "exitY", "entryX", "entryY",
                    "exitDx", "exitDy", "entryDx", "entryDy")
REQUIRED_EDGE_KEYS = {"edgeStyle": "orthogonalEdgeStyle",
                      "jumpStyle": "arc", "jumpSize": "6"}
# Shapes whose outline is not a rectangle, with the perimeter they need.
# The bare tokens ellipse, rhombus and triangle set their perimeter themselves.
SHAPE_PERIMETER = {
    "ellipse": "ellipsePerimeter", "doubleEllipse": "ellipsePerimeter",
    "rhombus": "rhombusPerimeter", "triangle": "trianglePerimeter",
    "hexagon": "hexagonPerimeter2", "parallelogram": "parallelogramPerimeter",
    "trapezoid": "trapezoidPerimeter", "callout": "calloutPerimeter",
    "step": "stepPerimeter", "cloud": "cloudPerimeter",
}
SELF_PERIMETER_TOKENS = {"ellipse", "rhombus", "triangle"}
THEME_TOKENS = {"blue", "green", "yellow", "orange", "red", "pink",
                "purple", "gray", "turquoise"}
MIN_GAP = 120
# Centres closer than this count as aligned; a larger offset gives the line a jog.
ALIGN_TOLERANCE = 1
MAX_LABEL_LINES = 3
ASAR_CANDIDATES = (
    "/Applications/draw.io.app/Contents/Resources/app.asar",
    os.path.expanduser("~/Applications/draw.io.app/Contents/Resources/app.asar"),
    "/opt/drawio/resources/app.asar",
    "/usr/lib/drawio/resources/app.asar",
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                 "draw.io", "resources", "app.asar"),
)
ASAR_WEBAPP = "drawio/src/main/webapp/"


def parse_style(style):
    """Split a style string into (bare tokens, key/value dict)."""
    tokens, keys = set(), {}
    for part in (style or "").split(";"):
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            keys[k] = v
        else:
            tokens.add(part)
    return tokens, keys


def decompress(text):
    """Decode a diagram saved with compressed="true" (base64, deflate, URL-encoding)."""
    raw = zlib.decompress(base64.b64decode(text), -15)
    return urllib.parse.unquote(raw.decode("utf-8"))


def drawio_names(path):
    """Read draw.io's app.asar and return (icon file paths, stencil styles).

    The file paths are complete. The stencil names are the ones the app's own
    scripts mention, which covers the common cloud icons but not every stencil,
    so a name missing from that set is only a warning. Each name maps to the
    shortest full style string the scripts use for it, or to None.
    """
    with open(path, "rb") as f:
        f.seek(4)
        data_start = 8 + struct.unpack("<I", f.read(4))[0]
        f.seek(12)
        header = json.loads(f.read(struct.unpack("<I", f.read(4))[0]))
        files, scripts = set(), []

        def walk(node, prefix):
            for name, child in node.get("files", {}).items():
                p = prefix + name
                if "files" in child:
                    walk(child, p + "/")
                else:
                    files.add(p)
                    if (name.endswith(".js") and "node_modules" not in p
                            and "offset" in child):
                        scripts.append(child)
        walk(header, "")
        stencils = {}
        for child in scripts:
            f.seek(data_start + int(child["offset"]))
            text = f.read(child["size"]).decode("utf-8", "ignore")
            for name in re.findall(r"mxgraph\.[a-z0-9_]+\.[A-Za-z0-9_]+", text):
                stencils.setdefault(name, None)
            # Full style strings, such as the import tables in extensions.min.js.
            for style in re.findall(r"[\"']((?:shape|[a-zA-Z]+=[^\"';]*;)[^\"']{0,400}?mxgraph\.[^\"']{0,300})[\"']", text):
                if "=" not in style or "\\" in style:
                    continue
                for name in re.findall(r"=(mxgraph\.[a-z0-9_]+\.[A-Za-z0-9_]+)(?=;|$)", style):
                    best = stencils.get(name)
                    if best is None or len(style) < len(best):
                        stencils[name] = style
    icons = {p[len(ASAR_WEBAPP):] for p in files
             if p.startswith(ASAR_WEBAPP + "img/lib/")}
    return icons, stencils


def find_asar(explicit):
    return explicit or next((p for p in ASAR_CANDIDATES if os.path.exists(p)), None)


def is_icon(tokens, keys):
    shape = keys.get("shape", "")
    return "image" in tokens or shape == "image" or shape.startswith("mxgraph.")


class Report:
    def __init__(self):
        self.lines, self.fails = [], 0

    def fail(self, where, msg):
        self.fails += 1
        self.lines.append(f"FAIL {where}: {msg}")

    def warn(self, where, msg):
        self.lines.append(f"WARN {where}: {msg}")


def centre(g):
    return g[0] + g[2] / 2, g[1] + g[3] / 2


def check_diagram(name, model, rep, names):
    root = model.find("root")
    if model.get("shadow") != "0":
        rep.fail(f"[{name}] mxGraphModel", 'set shadow="0" (flat look)')
    if root is None:
        rep.fail(f"[{name}]", "no <root> element")
        return

    by_id, order = {}, {}
    for i, el in enumerate(root):
        cid = el.get("id")
        if cid is None:
            continue
        if cid in by_id:
            rep.fail(f"[{name}] {cid}", "cell id is used twice")
        by_id[cid] = el
        order[cid] = i

    def cell_of(el):
        return el if el.tag == "mxCell" else el.find("mxCell")

    def geom(cid):
        c = cell_of(by_id[cid]) if cid in by_id else None
        g = c.find("mxGeometry") if c is not None else None
        if g is None:
            return None
        return tuple(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))

    edges_by_parent = {}
    flows = []
    for el in root:
        cid = el.get("id")
        cell = cell_of(el)
        if cell is None:
            continue
        where = f"[{name}] {cid}"
        tokens, keys = parse_style(cell.get("style"))

        for bad in ("shadow", "sketch", "comic", "glass"):
            if keys.get(bad) == "1":
                rep.fail(where, f"{bad}=1 breaks the flat look")
        if keys.get("gradientColor", "none") not in ("none", ""):
            rep.fail(where, "gradientColor breaks the flat look")
        if tokens & THEME_TOKENS:
            rep.fail(where, f"theme class {sorted(tokens & THEME_TOKENS)} adds shadow, glass and gradient")

        if cell.get("edge") == "1":
            parent = cell.get("parent")
            edges_by_parent.setdefault(parent, []).append(order[cid])
            src, tgt = cell.get("source"), cell.get("target")
            if not src or not tgt:
                rep.fail(where, "edge needs both source and target")
            for end in (src, tgt):
                if end and end not in by_id:
                    rep.fail(where, f"source/target '{end}' does not exist")
            fixed = [k for k in FIXED_POINT_KEYS if k in keys]
            if fixed:
                rep.warn(where, f"fixed connection point {fixed}; allowed only if the user asked")
            g = cell.find("mxGeometry")
            if src and tgt and g is not None:
                for p in g.findall("mxPoint"):
                    if p.get("as") in ("sourcePoint", "targetPoint"):
                        rep.fail(where, f"{p.get('as')} on an edge that connects two shapes")
            for k, v in REQUIRED_EDGE_KEYS.items():
                if keys.get(k) != v:
                    rep.fail(where, f"edge style needs {k}={v}")
            label = cell.get("value") or ""
            lines = label.replace("<br/>", "\n").replace("<br>", "\n").count("\n") + 1 if label else 0
            if lines > MAX_LABEL_LINES:
                rep.warn(where, f"label has {lines} lines; keep it to {MAX_LABEL_LINES} and move the rest into a note")
            # Spacing between the two shapes of an edge (rule: at least 80 px).
            if src in by_id and tgt in by_id:
                a, b = geom(src), geom(tgt)
                if a and b and cell_of(by_id[src]).get("parent") == cell_of(by_id[tgt]).get("parent"):
                    gap_x = max(b[0] - (a[0] + a[2]), a[0] - (b[0] + b[2]))
                    gap_y = max(b[1] - (a[1] + a[3]), a[1] - (b[1] + b[3]))
                    gap = max(gap_x, gap_y)
                    if gap < MIN_GAP:
                        rep.warn(where, f"only {gap:.0f} px between {src} and {tgt}; the minimum is {MIN_GAP}")
                    # Side by side or above each other: the centres must line
                    # up, or draw.io adds a small jog to a line that could be straight.
                    (ax, ay), (bx, by) = centre(a), centre(b)
                    has_points = g is not None and g.find("Array") is not None
                    if not has_points:
                        if gap_x > 0 and gap_y < 0 and abs(ay - by) > ALIGN_TOLERANCE:
                            rep.warn(where, f"{src} and {tgt} sit side by side but their centres differ by {abs(ay - by):.0f} px vertically; align the centres (not the tops) for a straight line")
                        if gap_y > 0 and gap_x < 0 and abs(ax - bx) > ALIGN_TOLERANCE:
                            rep.warn(where, f"{src} and {tgt} sit above each other but their centres differ by {abs(ax - bx):.0f} px horizontally; align the centres (not the left edges) for a straight line")
                    if a and b:
                        flows.append((cid, centre(a), centre(b)))
            continue

        if cell.get("vertex") != "1":
            continue
        shape = keys.get("shape") or next((t for t in tokens if t in SHAPE_PERIMETER), None)
        need = SHAPE_PERIMETER.get(shape)
        if need and not (shape in SELF_PERIMETER_TOKENS and shape in tokens) and keys.get("perimeter") != need:
            rep.fail(where, f"shape {shape} needs perimeter={need}")
        if is_icon(tokens, keys) and names is not None:
            icons, stencils = names
            image = keys.get("image", "")
            if image.startswith("img/lib/") and image not in icons:
                rep.fail(where, f"icon path {image} does not exist in draw.io; the icon renders empty. Look it up with --find")
            for key in ("shape", "resIcon"):
                stencil = keys.get(key, "")
                if stencil.startswith("mxgraph.") and stencil not in stencils:
                    rep.warn(where, f"stencil {stencil} is not in the names this script knows; look it up with --find, or check it in draw.io")

    # Two edges that run the same way but swap order between their ends will
    # cross. Swapping two shapes usually removes the crossing.
    for i, (e1, s1, t1) in enumerate(flows):
        for e2, s2, t2 in flows[i + 1:]:
            if s1 == s2 or t1 == t2:
                continue
            for axis, across in ((0, 1), (1, 0)):
                forward = all(t[axis] - s[axis] > 0 for s, t in ((s1, t1), (s2, t2)))
                backward = all(t[axis] - s[axis] < 0 for s, t in ((s1, t1), (s2, t2)))
                if not (forward or backward):
                    continue
                d_src, d_tgt = s1[across] - s2[across], t1[across] - t2[across]
                if d_src * d_tgt < 0:
                    rep.warn(f"[{name}] {e1}, {e2}", "these edges swap order between their ends and probably cross; swap the two targets (or the two sources) to remove the crossing")

    # Drawing order: every icon after all edges that share its parent.
    for el in root:
        cell = cell_of(el)
        if cell is None or cell.get("vertex") != "1":
            continue
        tokens, keys = parse_style(cell.get("style"))
        if not is_icon(tokens, keys):
            continue
        later = [i for i in edges_by_parent.get(cell.get("parent"), []) if i > order[el.get("id")]]
        if later:
            rep.fail(f"[{name}] {el.get('id')}", "icon comes before an edge with the same parent, so the line is drawn over it")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--find", metavar="TERM", nargs="+", help="list icon paths and stencil names that contain each TERM, then stop")
    ap.add_argument("--drawio-asar", help="path to draw.io's app.asar, for the icon path check")
    ap.add_argument("--expect-tabs", help="comma-separated tab names, in order, that the file should have")
    args = ap.parse_args()

    asar = find_asar(args.drawio_asar)
    names = drawio_names(asar) if asar else None

    if args.find:
        if names is None:
            sys.exit("draw.io desktop not found; pass --drawio-asar, or use the names from the draw.io sidebar")
        icons, stencils = names
        for raw in args.find:
            term = raw.lower().replace(" ", "_")
            hits = sorted(n for n in set(icons) | set(stencils) if term in n.lower())
            print(f"== {raw}")
            for n in hits[:40]:
                if n in icons:
                    print(f"image={n}")
                else:
                    print(f"{n}\n    style: {stencils[n]}" if stencils[n] else n)
            if not hits:
                print(f"Nothing matches '{raw}'. Try a shorter term, or use the name from the draw.io sidebar.")
            elif len(hits) > 40:
                print(f"... {len(hits) - 40} more; use a longer term.")
        return
    if not args.file:
        ap.error("give a .drawio file, or --find TERM")

    rep = Report()
    tree = ET.parse(args.file)
    mxfile = tree.getroot()
    if names is None:
        rep.warn("icons", "draw.io desktop not found; icon paths and stencil names were not checked")

    if mxfile.tag == "mxGraphModel":
        diagrams = [("(single)", mxfile)]
    else:
        diagrams = []
        seen_ids, seen_names = set(), set()
        for d in mxfile.findall("diagram"):
            name = d.get("name") or "(no name)"
            for attr, seen in (("id", seen_ids), ("name", seen_names)):
                v = d.get(attr)
                if not v:
                    rep.fail(f"[{name}]", f"<diagram> has no {attr}")
                elif v in seen:
                    rep.fail(f"[{name}]", f"<diagram> {attr} '{v}' is used twice")
                seen.add(v)
            model = d.find("mxGraphModel")
            if model is None and (d.text or "").strip():
                rep.fail(f"[{name}]", "diagram is compressed; save it as plain XML")
                model = ET.fromstring(decompress(d.text.strip()))
            if model is None:
                rep.fail(f"[{name}]", "diagram has no mxGraphModel")
                continue
            diagrams.append((name, model))
        if mxfile.get("compressed") == "true":
            rep.fail("mxfile", 'compressed="true"; save it as plain XML')

    if args.expect_tabs:
        want = [t.strip() for t in args.expect_tabs.split(",")]
        have = [n for n, _ in diagrams]
        if want != have:
            rep.fail("tabs", f"expected {want}, found {have}")

    for name, model in diagrams:
        check_diagram(name, model, rep, names)

    print("\n".join(rep.lines) if rep.lines else "No findings.")
    print(f"{len(diagrams)} tab(s), {rep.fails} failure(s), {len(rep.lines) - rep.fails} warning(s).")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
