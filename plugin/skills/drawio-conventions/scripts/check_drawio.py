#!/usr/bin/env python3
"""Run the mechanical part of the drawio-conventions checklist over a file.

Usage: check_drawio.py <file.drawio> [--drawio-asar PATH] [--expect-tabs NAME,NAME] [--no-render]
       check_drawio.py --find TERM [TERM ...]   list draw.io icon paths and stencil names per TERM

It reads the file from disk, so it checks what was really written, not what
the caller meant to write. It covers the general rules (A and B, flat look,
drawing order, file format, tabs, arrow heads, group resizing, note autosize, layout of connected shapes, lines that share
a start point, icon names, icon label position, label fit, note size). When
draw.io desktop is installed, it also renders each tab to SVG and reports
lines that run on top of each other and lines that run through a label. It does not
know the other house-style values, because a user can replace them: compare those by
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
import shutil
import struct
import subprocess
import sys
import tempfile
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
# The house style lets the gap vary from 80 to 120 px; below 80 is too tight.
MIN_GAP = 80
# Two edge ends closer than this on one side of a shape draw as one line.
SAME_POINT = 10
# Centres closer than this count as aligned; a larger offset gives the line a jog.
ALIGN_TOLERANCE = 1
MAX_LABEL_LINES = 3
# Rough text width per character at fontSize 12. Measured on draw.io's
# rendering of Helvetica: about 5.5 px, so this keeps a small margin.
CHAR_WIDTH = 6
# Two straight stretches of different lines closer than this read as one line.
OVERLAP_DISTANCE = 4
# ... and closer than this as one thick line.
CLOSE_DISTANCE = 12
MIN_OVERLAP = 10
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


def find_drawio_binary(asar):
    """The draw.io program that belongs to app.asar, for rendering."""
    if asar:
        res = os.path.dirname(os.path.abspath(asar))
        for rel in (("..", "MacOS", "draw.io"), ("..", "drawio"), ("..", "draw.io.exe")):
            cand = os.path.normpath(os.path.join(res, *rel))
            if os.path.isfile(cand):
                return cand
    return shutil.which("drawio") or shutil.which("draw.io")


def path_segments(d):
    """Return the straight segments of an SVG path as (x1, y1, x2, y2).

    Curves and arcs, such as the line jumps, only move the current point.
    """
    tokens = re.findall(r"[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?", d)
    arity = {"M": 2, "L": 2, "Q": 4, "C": 6, "A": 7, "Z": 0}
    segs, cmd, cur, nums = [], None, None, []
    for tok in tokens + ["Z"]:
        if tok.isalpha():
            cmd, nums = tok.upper(), []
            if cmd == "Z":
                cur = None
            continue
        nums.append(float(tok))
        if cmd and arity.get(cmd) and len(nums) == arity[cmd]:
            end = (nums[-2], nums[-1])
            if cmd == "L" and cur:
                segs.append((cur[0], cur[1], end[0], end[1]))
            cur, nums = end, []
            if cmd == "M":
                cmd = "L"
    return segs


def rendered(binary, path, page, edge_ids):
    """Render one tab with draw.io.

    Return ({edge id: [segments]}, {cell id: label box}). A label box is
    (x0, y0, x1, y1) around the text as draw.io draws it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "page.svg")
        subprocess.run([binary, "-x", "-f", "svg", "-p", str(page), "-o", out, path],
                       capture_output=True, timeout=180, check=False)
        if not os.path.exists(out):
            raise RuntimeError("draw.io wrote no SVG; a sandbox may block it")
        svg = ET.parse(out).getroot()
    lines, labels = {}, {}

    def walk(el, owner):
        owner = el.get("data-cell-id", owner)
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "path" and owner in edge_ids and owner not in lines:
            d = el.get("d", "")
            if "Z" not in d.upper():  # arrow heads are closed shapes
                lines[owner] = path_segments(d)
        if tag == "switch" and owner:
            box = label_box(el)
            if box:
                labels[owner] = box
        for child in el:
            walk(child, owner)
    walk(svg, None)
    return lines, labels


def label_box(switch):
    """The box around a label's text, from the fallback image that draw.io
    writes after each HTML label. The image is as wide as the label's room,
    which for a wrapped label is the whole shape, so narrow it to the text."""
    image = next((c for c in switch if c.tag.endswith("image")), None)
    if image is None:
        return None
    try:
        x, y, w, h = (float(image.get(k)) for k in ("x", "y", "width", "height"))
    except (TypeError, ValueError):
        return None
    divs = [d for d in switch.iter() if d.tag.endswith("div")]
    if divs:
        inner = divs[-1]
        texts = [inner.text or ""] + [c.tail or "" for c in inner]
        size = re.search(r"font-size:\s*([\d.]+)px", inner.get("style", ""))
        size = float(size.group(1)) if size else 12
        text_w = max(len(t.strip()) for t in texts) * CHAR_WIDTH * size / 12
        if 0 < text_w < w:
            align = re.search(r"text-align:\s*(\w+)", divs[1].get("style", "") if len(divs) > 1 else "")
            align = align.group(1) if align else "center"
            if align == "left":
                w = text_w
            elif align == "right":
                x, w = x + w - text_w, text_w
            else:
                x, w = x + (w - text_w) / 2, text_w
    return (x, y, x + w, y + h)


def crosses_box(seg, box, inset=3):
    """True when a straight segment passes through the box (Liang-Barsky clip).

    The inset ignores the box's outer pixels: draw.io's label box includes the
    extra line height above and below the text."""
    x1, y1, x2, y2 = seg
    bx0, by0, bx1, by1 = box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset
    if bx0 >= bx1 or by0 >= by1:
        return False
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def overlapping_lines(lines):
    """Return {(edge, edge): (distance, length)} for straight stretches of two
    lines that run along each other closer than CLOSE_DISTANCE."""
    flat = []
    for eid, segs in lines.items():
        for x1, y1, x2, y2 in segs:
            if abs(y1 - y2) < 0.5:
                flat.append(("h", y1, min(x1, x2), max(x1, x2), eid))
            elif abs(x1 - x2) < 0.5:
                flat.append(("v", x1, min(y1, y2), max(y1, y2), eid))
    found = {}
    for i, a in enumerate(flat):
        for b in flat[i + 1:]:
            if a[0] != b[0] or a[4] == b[4]:
                continue
            dist = abs(a[1] - b[1])
            length = min(a[3], b[3]) - max(a[2], b[2])
            if dist < CLOSE_DISTANCE and length >= MIN_OVERLAP:
                key = tuple(sorted((a[4], b[4])))
                old = found.get(key)
                if old is None or (dist, -length) < (old[0], -old[1]):
                    found[key] = (dist, length)
    return found


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


def attach(shape, aim, waypoint):
    """Return (side, position along that side) where an edge leaves `shape`.

    `aim` is the edge's waypoint next to the shape, or the other shape's
    centre. With a waypoint, draw.io's orthogonal router leaves the shape at the
    waypoint's height (or x) when that lies within the shape, and from the
    middle of the top or bottom side when it lies beyond a corner. Without a
    waypoint, it starts from the middle of the side that faces the other shape.
    """
    x, y, w, h = shape
    cx, cy = centre(shape)
    if waypoint:
        if y <= aim[1] <= y + h and not x <= aim[0] <= x + w:
            return ("right" if aim[0] > cx else "left"), aim[1]
        if x <= aim[0] <= x + w and not y <= aim[1] <= y + h:
            return ("bottom" if aim[1] > cy else "top"), aim[0]
        if x <= aim[0] <= x + w and y <= aim[1] <= y + h:
            return None  # a waypoint inside the shape
        # A waypoint beyond a corner: in renders, draw.io always left from the
        # middle of the top or bottom side, also when the waypoint lay further
        # sideways than up or down.
        return ("bottom" if aim[1] > cy else "top"), cx
    dx, dy = aim[0] - cx, aim[1] - cy
    if abs(dx) >= abs(dy):
        return ("right" if dx > 0 else "left"), cy
    return ("bottom" if dy > 0 else "top"), cx


def text_lines(label):
    """Split a label into its lines, without HTML tags."""
    label = re.sub(r"<br\s*/?>|</div>|</p>", "\n", label or "")
    label = re.sub(r"<[^>]+>", "", label).replace("&nbsp;", " ")
    return [line for line in label.split("\n") if line.strip()]


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
    ends = {}  # (shape id, side) -> [(edge id, position along the side)]
    turns = {}  # (shape id, side) -> [(edge id, waypoint, centre of the other shape)]
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
            edges_by_parent.setdefault(cell.get("parent"), []).append(cid)
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
            if keys.get("startArrow", "none") not in ("none", "") and keys.get("endArrow") != "none":
                rep.fail(where, "edge has an arrow head at both ends; draw one edge per direction, so each line shows one flow")
            label = cell.get("value") or ""
            lines = len(text_lines(label))
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
                    if a and b and cell.get("parent") == cell_of(by_id[src]).get("parent"):
                        pts = [(float(p.get("x", 0)), float(p.get("y", 0)))
                               for p in (g.find("Array") if has_points else [])]
                        for shape_id, shape, aim, wp in (
                                (src, a, pts[0] if pts else centre(b), bool(pts)),
                                (tgt, b, pts[-1] if pts else centre(a), bool(pts))):
                            spot = attach(shape, aim, wp)
                            if spot:
                                ends.setdefault((shape_id, spot[0]), []).append((cid, spot[1], wp))
                            if spot and len(pts) == 1:
                                far = centre(b) if shape is a else centre(a)
                                turns.setdefault((shape_id, spot[0]), []).append((cid, pts[0], far))
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
        if is_icon(tokens, keys) and cell.get("value"):
            if keys.get("verticalLabelPosition") != "bottom" or keys.get("labelPosition", "center") != "center":
                rep.fail(where, "icon label is not under the icon; set verticalLabelPosition=bottom;verticalAlign=top;labelPosition=center;align=center")
        is_note = "text" in tokens or keys.get("shape") == "note"
        label_inside = (keys.get("verticalLabelPosition", "middle") == "middle"
                        and keys.get("labelPosition", "center") == "center")
        lines = text_lines(cell.get("value"))
        g = geom(cid)
        # An edge label cell has a relative geometry of size 0; it sits on its line.
        on_edge = (cell.find("mxGeometry") is not None
                   and cell.find("mxGeometry").get("relative") == "1")
        if lines and g and not is_note and not on_edge and keys.get("container") != "1":
            char_w = CHAR_WIDTH * float(keys.get("fontSize") or 12) / 12
            widest = max(len(line) for line in lines) * char_w
            if is_icon(tokens, keys):
                limit = max(2.5 * g[2], 160)
                if widest > limit:
                    rep.warn(where, f"icon label is about {widest:.0f} px wide; split it over 2 lines with <br> (3 at most), each under about {limit:.0f} px")
                if len(lines) > MAX_LABEL_LINES:
                    rep.warn(where, f"icon label has {len(lines)} lines; keep it to {MAX_LABEL_LINES}")
            elif label_inside:
                room = max(g[2] - 10, 1)
                if keys.get("whiteSpace") == "wrap":
                    rows = sum(max(1, -(-int(len(line) * char_w) // int(room))) for line in lines)
                    word = max(len(w) for line in lines for w in line.split()) * char_w
                    if word > room:
                        rep.warn(where, f"a word in the label is about {word:.0f} px wide and the shape only {g[2]:.0f} px; widen the shape or shorten the word")
                else:
                    rows = len(lines)
                    if widest > room:
                        rep.warn(where, f"label is about {widest:.0f} px wide and runs over the {g[2]:.0f} px shape; split it with <br> or widen the shape")
                line_h = 1.2 * float(keys.get("fontSize") or 12)
                if rows > MAX_LABEL_LINES:
                    rep.warn(where, f"label needs about {rows} lines; keep it to {MAX_LABEL_LINES} by widening the shape, shortening the label or moving detail into a note")
                elif rows * line_h + 10 > g[3]:
                    rep.warn(where, f"label needs about {rows} lines but the shape is only {g[3]:.0f} px high, so the text runs over its border; make the shape taller or wider")
        if is_note and keys.get("autosize") == "1":
            rep.warn(where, "autosize=1 makes draw.io resize the note every time its text is edited; remove it and give the note a fixed size")
        if cell.get("vertex") == "1" and keys.get("container") == "1" and keys.get("recursiveResize") != "0":
            rep.warn(where, "group without recursiveResize=0: resizing it in draw.io also resizes and moves the shapes inside; add recursiveResize=0")
        # A note sized to fit its text, not to match the other notes.
        if is_note and cell.get("value"):
            g = geom(cid)
            lines = text_lines(cell.get("value"))
            if g and lines:
                chars = max(len(line) for line in lines)
                rows = sum(-(-len(line) * CHAR_WIDTH // max(g[2] - 10, 1)) for line in lines)
                fit_w, fit_h = chars * CHAR_WIDTH + 20, rows * 18 + 20
                if g[3] > 2 * fit_h and g[3] - fit_h > 40 or g[2] > 2 * fit_w and g[2] - fit_w > 60:
                    rep.warn(where, f"note is {g[2]:.0f} x {g[3]:.0f} px but its text needs about {min(g[2], fit_w):.0f} x {fit_h:.0f}; size each note to its own text")

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

    # Lines that leave or enter one side of a shape at the same point overlap
    # and read as one line. A waypoint per edge at its own height spreads them.
    for (shape_id, side), spots in ends.items():
        spots.sort(key=lambda s: s[1])
        for (e1, p1, w1), (e2, p2, w2) in zip(spots, spots[1:]):
            if p2 - p1 < SAME_POINT:
                # With waypoints on both edges the shared point is certain;
                # without, the side is a guess.
                (rep.fail if w1 and w2 else rep.warn)(f"[{name}] {e1}, {e2}", f"these edges meet {shape_id} at the same point on its {side} side and overlap; give each a waypoint at its own height within the side, for example 1/4, 1/2, 3/4")

    # Edges that spread along one side with one waypoint each still overlap
    # when two of them turn the same way at the same distance from the shape:
    # draw.io runs both along that row towards their other shape. This needs
    # no render, so it also works where draw.io cannot run.
    for (shape_id, side), items in turns.items():
        across = 1 if side in ("top", "bottom") else 0  # the row is a y (or an x)
        along = 1 - across
        for i, (e1, w1, f1) in enumerate(items):
            for e2, w2, f2 in items[i + 1:]:
                if abs(w1[across] - w2[across]) >= OVERLAP_DISTANCE:
                    continue
                d1, d2 = f1[along] - w1[along], f2[along] - w2[along]
                if d1 * d2 <= 0:
                    continue  # they turn in opposite directions
                lo = max(min(w1[along], f1[along]), min(w2[along], f2[along]))
                hi = min(max(w1[along], f1[along]), max(w2[along], f2[along]))
                if hi - lo >= MIN_OVERLAP:
                    rep.fail(f"[{name}] {e1}, {e2}", f"these edges leave {shape_id} on its {side} side and turn the same way at the same distance, so they run on top of each other for about {hi - lo:.0f} px; nest the turns: the edge that leaves nearest the corner turns first, about 40 px out, the next one 30 px further")

    # An icon's label sits under the picture, so a line that leaves or enters
    # an icon at the bottom runs through the label. This needs no render.
    through_label = set()
    for (shape_id, side), spots in ends.items():
        if side != "bottom" or shape_id not in by_id:
            continue
        icell = cell_of(by_id[shape_id])
        tokens, keys = parse_style(icell.get("style"))
        if not (is_icon(tokens, keys) and icell.get("value")
                and keys.get("verticalLabelPosition") == "bottom"):
            continue
        for eid, _, wp in spots:
            if wp:  # certain, so the render need not report it again
                through_label.add((eid, shape_id))
            (rep.fail if wp else rep.warn)(f"[{name}] {eid}", f"this line meets icon {shape_id} at the bottom, where its label is, and runs through the text; let it reach the icon from the left, right or top, with a waypoint if needed, or move a shape")

    # Drawing order. draw.io draws a group together with everything in it, at
    # the group's place among its siblings. So an edge must come before the
    # icons of its own parent, and before every group that holds icons.
    parent_of, children = {}, {}
    for el in root:
        cell = cell_of(el)
        if cell is not None and el.get("id"):
            parent_of[el.get("id")] = cell.get("parent")
            children.setdefault(cell.get("parent"), []).append(el.get("id"))
    drawn = {}

    def walk(pid):
        for kid in children.get(pid, []):
            if kid not in drawn:
                drawn[kid] = len(drawn)
                walk(kid)
    walk(None)
    for el in root:
        cell = cell_of(el)
        icon = el.get("id")
        if cell is None or cell.get("vertex") != "1" or icon not in drawn:
            continue
        tokens, keys = parse_style(cell.get("style"))
        if not is_icon(tokens, keys):
            continue
        holder, seen = icon, set()
        while parent_of.get(holder) is not None and holder not in seen:
            seen.add(holder)
            parent = parent_of[holder]
            later = [e for e in edges_by_parent.get(parent, []) if drawn.get(e, -1) > drawn[icon]]
            if later and holder == icon:
                rep.fail(f"[{name}] {icon}", f"icon comes before edge {later[0]} with the same parent, so the line is drawn over it")
            elif later:
                rep.fail(f"[{name}] {icon}", f"edge {later[0]} comes after group {holder}, which holds this icon, so the line is drawn over everything in the group; write the edge before the group")
            holder = parent

    # An edge belongs to the parent of whichever end is drawn later. Drawn
    # anywhere else, a group's fill hides the line, or the line covers the
    # group's icons.
    for el in root:
        cell = cell_of(el)
        if cell is None or cell.get("edge") != "1":
            continue
        ends = [parent_of.get(cell.get(k)) for k in ("source", "target")]
        if None in ends:
            continue
        want = max(ends, key=lambda p: drawn.get(p, -1))
        group = by_id.get(want)
        if cell.get("parent") == want or group is None or cell_of(group).get("vertex") != "1":
            continue
        _, gkeys = parse_style(cell_of(group).get("style"))
        where = f"[{name}] {el.get('id')}"
        msg = f"an end of this edge is in group {want}, but the edge is not; set parent=\"{want}\" (waypoints relative to the group) and write it before the group's icons"
        if gkeys.get("fillColor", "#ffffff").lower() != "none":
            rep.fail(where, msg + ", or the group's fill hides the line")
        else:
            rep.warn(where, msg)
    return through_label


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--find", metavar="TERM", nargs="+", help="list icon paths and stencil names that contain each TERM, then stop")
    ap.add_argument("--drawio-asar", help="path to draw.io's app.asar, for the icon path check")
    ap.add_argument("--expect-tabs", help="comma-separated tab names, in order, that the file should have")
    ap.add_argument("--no-render", action="store_true", help="skip rendering with draw.io, and with it the check for lines on top of each other")
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

    known = {}  # tab -> (edge, icon) pairs already reported as through the label
    for name, model in diagrams:
        known[name] = check_diagram(name, model, rep, names) or set()

    # Lines on top of each other only show in the routes draw.io computes, so
    # render each tab and compare the straight stretches of its lines.
    binary = None if args.no_render else find_drawio_binary(asar)
    if not args.no_render and binary is None:
        rep.warn("render", "draw.io desktop not found; lines on top of each other were not checked")
    for page, (name, model) in enumerate(diagrams if binary else [], start=1):
        edge_ids = {c.get("id") for c in model.iter("mxCell") if c.get("edge") == "1"}
        if len(edge_ids) < 2:
            continue
        try:
            lines, labels = rendered(binary, os.path.abspath(args.file), page, edge_ids)
        except (OSError, RuntimeError, subprocess.SubprocessError, ET.ParseError) as err:
            rep.warn(f"[{name}] render", f"draw.io could not render this tab ({err}); lines on top of each other and lines through labels were not checked")
            continue
        for (e1, e2), (dist, length) in sorted(overlapping_lines(lines).items()):
            if dist < OVERLAP_DISTANCE:
                rep.fail(f"[{name}] {e1}, {e2}", f"these lines run on top of each other for about {length:.0f} px, so one hides the other; move a shape, or give one of them a waypoint so they run at least 30 px apart")
            else:
                rep.warn(f"[{name}] {e1}, {e2}", f"these lines run only {dist:.0f} px apart for about {length:.0f} px and read as one thick line; keep parallel lines at least 30 px apart")
        # A line through a label hides the text. An edge's own label sits on
        # its own line by design, so skip that pair.
        parent = {c.get("id"): c.get("parent") for c in model.iter("mxCell")}
        for owner, box in sorted(labels.items()):
            for eid, segs in sorted(lines.items()):
                if eid == owner or parent.get(owner) == eid or (eid, owner) in known.get(name, ()):
                    continue
                if not any(crosses_box(seg, box) for seg in segs):
                    continue
                if owner in edge_ids or parent.get(owner) in edge_ids:
                    fix = "move that label along its own line (mxGeometry x between -1 and 1), or give this line a waypoint around it"
                else:
                    fix = "give this line a waypoint around the label, let it reach its shape from another side, or move a shape"
                rep.fail(f"[{name}] {eid}", f"this line runs through the label of {owner}, so the text is hard to read; {fix}")

    print("\n".join(rep.lines) if rep.lines else "No findings.")
    print(f"{len(diagrams)} tab(s), {rep.fails} failure(s), {len(rep.lines) - rep.fails} warning(s).")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
