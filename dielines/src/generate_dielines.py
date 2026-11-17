#!/usr/bin/env python3
"""
L'Adresse packaging — die-line (tracé de découpe) generator.

Builds parametric, physically-coherent die-lines for the six L'Adresse boxes
and exports each one as layered SVG + PDF at 1:1 scale (millimetres).

  DECOUPE   (cut)      solid black 0.25 mm stroke, closed continuous paths
  RAINAGE   (crease)   dashed black 0.25 mm stroke, merged, no duplicates
  MARQUAGE  (marking)  brand text/logo converted to filled outlines (not cut)
  INFOS     (info)     title block, legend, scale bar (outlined text, not cut)

The *_production files contain only DECOUPE + RAINAGE.

Geometry: every panel/flap is a polygon; the cut outline is their boolean
union (so there are no overlapping or duplicated cut lines), cleaned of
collinear points, and every circular feature (fillets, windows, holes,
thumb notches) is re-emitted as true cubic Bézier arcs.

Requires: shapely, fonttools.   Run:  python3 generate_dielines.py
"""
import math
import os
import zlib

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STROKE = 0.25          # mm
DASH = (3.0, 1.5)      # mm, crease dash pattern
SEG = 256              # polygon resolution for a full circle (internal only)
MARGIN = 15.0          # mm around the drawing

FONT_DIR = "/usr/share/fonts/truetype"
F_SERIF = FONT_DIR + "/freefont/FreeSerif.ttf"
F_SERIF_I = FONT_DIR + "/freefont/FreeSerifItalic.ttf"
F_SANS = FONT_DIR + "/liberation/LiberationSans-Regular.ttf"
F_SANS_B = FONT_DIR + "/liberation/LiberationSans-Bold.ttf"


# --------------------------------------------------------------------------
# small vector helpers
# --------------------------------------------------------------------------
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1]
def cross(a, b): return a[0] * b[1] - a[1] * b[0]
def norm(a):
    L = math.hypot(*a)
    return (a[0] / L, a[1] / L)


def arc_cubics(c, r, a0, sweep):
    """Cubic Bézier pieces (each <= 90 deg) for an arc. Returns list of C cmds."""
    n = max(1, int(math.ceil(abs(sweep) / (math.pi / 2) - 1e-9)))
    phi = sweep / n
    k = 4.0 / 3.0 * math.tan(phi / 4.0)
    cmds = []
    a = a0
    for _ in range(n):
        b = a + phi
        p0 = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        p3 = (c[0] + r * math.cos(b), c[1] + r * math.sin(b))
        p1 = (p0[0] - k * r * math.sin(a), p0[1] + k * r * math.cos(a))
        p2 = (p3[0] + k * r * math.sin(b), p3[1] - k * r * math.cos(b))
        cmds.append(["C", *p1, *p2, *p3])
        a = b
    return cmds


def xform(cmds, tf):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append(["Z"])
            continue
        pts = [tf((c[i], c[i + 1])) for i in range(1, len(c), 2)]
        out.append([c[0]] + [v for p in pts for v in p])
    return out


def tf_place(cx, cy, rot_deg=0.0, scale=1.0):
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    return lambda p: (cx + scale * (ca * p[0] - sa * p[1]),
                      cy + scale * (sa * p[0] + ca * p[1]))


# --------------------------------------------------------------------------
# fonts -> outlines
# --------------------------------------------------------------------------
class _Pen(BasePen):
    def __init__(self, gs, tf):
        super().__init__(gs)
        self.c, self.tf = [], tf

    def _moveTo(self, p): self.c.append(["M", *self.tf(p)])
    def _lineTo(self, p): self.c.append(["L", *self.tf(p)])
    def _curveToOne(self, a, b, p): self.c.append(["C", *self.tf(a), *self.tf(b), *self.tf(p)])

    def _qCurveToOne(self, a, p):          # exact quadratic -> cubic
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2 / 3 * (a[0] - p0[0]), p0[1] + 2 / 3 * (a[1] - p0[1]))
        c2 = (p[0] + 2 / 3 * (a[0] - p[0]), p[1] + 2 / 3 * (a[1] - p[1]))
        self.c.append(["C", *self.tf(c1), *self.tf(c2), *self.tf(p)])

    def _closePath(self): self.c.append(["Z"])
    def _endPath(self): self.c.append(["Z"])


class Font:
    _cache = {}

    def __new__(cls, path):
        if path not in cls._cache:
            o = super().__new__(cls)
            o.tt = TTFont(path)
            o.gs = o.tt.getGlyphSet()
            o.cmap = o.tt.getBestCmap()
            o.upm = o.tt["head"].unitsPerEm
            o.hmtx = o.tt["hmtx"]
            cls._cache[path] = o
        return cls._cache[path]

    def _g(self, ch): return self.cmap.get(ord(ch), ".notdef")

    def width(self, text, size):
        return sum(self.hmtx[self._g(ch)][0] for ch in text) * size / self.upm

    def outline(self, text, size, place, anchor="middle"):
        """place: function (x,y)->(x,y) in die coords; text baseline at local y=0."""
        w = self.width(text, size)
        x = {"start": 0.0, "middle": -w / 2, "end": -w}[anchor]
        s = size / self.upm
        cmds = []
        for ch in text:
            g = self._g(ch)
            ox = x
            pen = _Pen(self.gs, lambda p, ox=ox: place((ox + p[0] * s, p[1] * s)))
            self.gs[g].draw(pen)
            cmds += pen.c
            x += self.hmtx[g][0] * s
        return cmds


# --------------------------------------------------------------------------
# brand marks (vector, Bézier)
# --------------------------------------------------------------------------
def ellipse_cmds(cx, cy, rx, ry):
    k = 0.5522847498
    return [["M", cx + rx, cy],
            ["C", cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry],
            ["C", cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy],
            ["C", cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry],
            ["C", cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy],
            ["Z"]]


def pin_cmds():
    """Location pin with coffee bean, unit circle radius 1, tip at (0,-2)."""
    s3 = math.sqrt(3) / 2
    c = [["M", 0, -2.0], ["L", s3, -0.5]]
    c += arc_cubics((0, 0), 1.0, math.radians(-30), math.radians(240))
    c += [["L", 0, -2.0], ["Z"]]
    c += ellipse_cmds(0, 0, 0.66, 0.66)                       # knock-out
    rot = tf_place(0, 0, -35)
    c += xform(ellipse_cmds(0, 0, 0.30, 0.47), rot)            # bean
    slit = [["M", 0.0, 0.40],
            ["C", -0.17, 0.15, 0.17, -0.15, 0.0, -0.40],
            ["C", 0.10, -0.15, -0.07, 0.15, 0.06, 0.40], ["Z"]]
    c += xform(slit, rot)
    return c


def heart_cmds():
    """Outline heart (♡), roughly 1 unit wide, centred on origin."""
    h = [["M", 0, -0.5],
         ["C", -0.1, -0.36, -0.55, -0.12, -0.55, 0.18],
         ["C", -0.55, 0.45, -0.2, 0.56, 0, 0.3],
         ["C", 0.2, 0.56, 0.55, 0.45, 0.55, 0.18],
         ["C", 0.55, -0.12, 0.1, -0.36, 0, -0.5], ["Z"]]
    inner = xform(h, lambda p: (p[0] * 0.72, p[1] * 0.70 + 0.03))
    return h + inner


# --------------------------------------------------------------------------
# die model
# --------------------------------------------------------------------------
class Die:
    def __init__(self, key, title, dims, notes=""):
        self.key, self.title, self.dims, self.notes = key, title, dims, notes
        self.parts = {}          # part -> list of polygons
        self.cutouts = {}        # part -> list of polygons removed
        self.creases = []
        self.slits = []          # explicit open cut lines
        self.circles = []
        self.marks = []          # list of cmd lists (filled, even-odd)

    # ---- primitive builders ------------------------------------------------
    def rpoly(self, pts, radii=None):
        radii = radii or {}
        n, out = len(pts), []
        for i, p in enumerate(pts):
            r = radii.get(i, 0)
            if r <= 0:
                out.append(p)
                continue
            u = norm(sub(pts[i - 1], p))
            v = norm(sub(pts[(i + 1) % n], p))
            th = math.acos(max(-1.0, min(1.0, dot(u, v))))
            t = r / math.tan(th / 2)
            c = add(p, mul(norm(add(u, v)), r / math.sin(th / 2)))
            p1, p2 = add(p, mul(u, t)), add(p, mul(v, t))
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
            d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
            ns = max(8, int(math.ceil(abs(d) / (2 * math.pi) * SEG)))
            for k in range(ns + 1):
                a = a1 + d * k / ns
                out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
            self.circles.append((c[0], c[1], r))
        return Polygon(out)

    def rect(self, x0, y0, x1, y1, r=0):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return self.rpoly(pts, {i: r for i in range(4)} if r else None)

    def circle(self, cx, cy, r):
        self.circles.append((cx, cy, r))
        return Polygon([(cx + r * math.cos(2 * math.pi * k / SEG),
                         cy + r * math.sin(2 * math.pi * k / SEG)) for k in range(SEG)])

    def panel(self, poly, part="main"): self.parts.setdefault(part, []).append(poly)
    def cutout(self, poly, part="main"): self.cutouts.setdefault(part, []).append(poly)
    def crease(self, x0, y0, x1, y1): self.creases.append(((x0, y0), (x1, y1)))
    def slit(self, x0, y0, x1, y1): self.slits.append(((x0, y0), (x1, y1)))

    # ---- marks ---------------------------------------------------------------
    def logo(self, cx, cy, s, rot=0, tagline=True):
        P = tf_place(cx, cy, rot)
        self.marks.append(Font(F_SERIF).outline("L’Adresse", s, P))
        R = 0.27 * s
        self.marks.append(xform(pin_cmds(), lambda p: P((p[0] * R, 0.86 * s + 2 * R + p[1] * R))))
        if tagline:
            self.marks.append(Font(F_SERIF_I).outline("– Artisan Coffee and World Kitchen –", 0.24 * s,
                                                      lambda p: P((p[0], p[1] - 0.40 * s))))

    def sweet(self, cx, cy, t, rot=0):
        P = tf_place(cx, cy, rot)
        fi = Font(F_SERIF_I)
        self.marks.append(fi.outline("Sweet moments.", t, lambda p: P((p[0], p[1] + 0.25 * t))))
        l2 = "Delivered with love "
        w = fi.width(l2, t) + 0.75 * t
        self.marks.append(fi.outline(l2, t, lambda p: P((p[0] - w / 2, p[1] - 1.05 * t)), "start"))
        hx = -w / 2 + fi.width(l2, t) + 0.33 * t
        self.marks.append(xform(heart_cmds(), lambda p: P((hx + p[0] * 0.62 * t, -1.05 * t + 0.33 * t + p[1] * 0.62 * t))))

    # ---- geometry finalisation ---------------------------------------------------
    def shapes(self):
        res = []
        for part, polys in self.parts.items():
            g = unary_union(polys)
            if self.cutouts.get(part):
                g = g.difference(unary_union(self.cutouts[part]))
            geoms = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
            assert len(geoms) == 1, f"{self.key}/{part}: outline is not one piece"
            assert geoms[0].is_valid, f"{self.key}/{part}: invalid outline"
            res.append(geoms[0])
        return res

    def _clean_ring(self, coords):
        pts = [tuple(p) for p in coords[:-1]]
        out = []
        for p in pts:
            if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6:
                out.append(p)
        if math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < 1e-6:
            out.pop()
        changed = True
        while changed:
            changed = False
            for i in range(len(out)):
                a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
                u, v = sub(b, a), sub(c, b)
                if abs(cross(norm(u), norm(v))) < 1e-7 and dot(u, v) > 0:
                    out.pop(i)
                    changed = True
                    break
        return out

    def _on(self, p, c):
        return abs(math.hypot(p[0] - c[0], p[1] - c[1]) - c[2]) < 1e-3

    def ring_to_cmds(self, coords):
        pts = self._clean_ring(coords)
        n = len(pts)
        circ = [[c for c in self.circles if self._on(p, c)] for p in pts]
        # full circle?
        for c in (circ[0] or []):
            if all(c in cl for cl in circ):
                return [["M", c[0] + c[2], c[1]]] + arc_cubics((c[0], c[1]), c[2], 0, 2 * math.pi) + [["Z"]]
        start = next((i for i in range(n) if not circ[i]), 0)
        pts = pts[start:] + pts[:start]
        circ = circ[start:] + circ[:start]
        pts.append(pts[0]); circ.append(circ[0])
        cmds = [["M", *pts[0]]]
        i = 0
        while i < n:
            best_j, best_c = i, None
            for c in circ[i]:
                j = i
                while j + 1 <= n and c in circ[j + 1]:
                    a0 = math.atan2(pts[j][1] - c[1], pts[j][0] - c[0])
                    a1 = math.atan2(pts[j + 1][1] - c[1], pts[j + 1][0] - c[0])
                    if abs((a1 - a0 + math.pi) % (2 * math.pi) - math.pi) > 0.45:
                        break
                    j += 1
                if j - i >= 2 and j > best_j:
                    best_j, best_c = j, c
            if best_c:
                c = best_c
                sweep = 0.0
                for k in range(i, best_j):
                    a0 = math.atan2(pts[k][1] - c[1], pts[k][0] - c[0])
                    a1 = math.atan2(pts[k + 1][1] - c[1], pts[k + 1][0] - c[0])
                    sweep += (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                a0 = math.atan2(pts[i][1] - c[1], pts[i][0] - c[0])
                arcs = arc_cubics((c[0], c[1]), c[2], a0, sweep)
                arcs[-1][5], arcs[-1][6] = pts[best_j]
                cmds += arcs
                i = best_j
            else:
                cmds.append(["L", *pts[i + 1]])
                i += 1
        if cmds[-1][0] == "L":
            cmds.pop()                      # closing segment is implied by Z
        cmds.append(["Z"])
        return cmds

    def cut_paths(self):
        paths = []
        for g in self.shapes():
            paths.append(self.ring_to_cmds(list(g.exterior.coords)))
            for h in g.interiors:
                paths.append(self.ring_to_cmds(list(h.coords)))
        for a, b in self.slits:
            paths.append([["M", *a], ["L", *b]])
        return paths

    def merged_creases(self):
        groups = {}
        for a, b in self.creases:
            d = norm(sub(b, a))
            if d[0] < -1e-9 or (abs(d[0]) < 1e-9 and d[1] < 0):
                d, a, b = mul(d, -1), b, a
            off = round(cross(d, a), 4)
            key = (round(d[0], 6), round(d[1], 6), off)
            t0, t1 = dot(a, d), dot(b, d)
            groups.setdefault(key, []).append((min(t0, t1), max(t0, t1)))
        out = []
        for (dx, dy, off), iv in groups.items():
            iv.sort()
            merged = [list(iv[0])]
            for s, e in iv[1:]:
                if s <= merged[-1][1] + 1e-6:
                    merged[-1][1] = max(merged[-1][1], e)
                else:
                    merged.append([s, e])
            nrm = (-dy, dx)
            for s, e in merged:
                base = mul(nrm, off)
                out.append((add(base, mul((dx, dy), s)), add(base, mul((dx, dy), e))))
        return out

    def validate(self):
        shapes = self.shapes()
        U = unary_union(shapes)
        for a, b in self.merged_creases():
            for t in (0.02, 0.5, 0.98):
                p = Point(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                assert U.buffer(1e-6).contains(p), f"{self.key}: crease {a}-{b} leaves the blank"
        return U.bounds


# --------------------------------------------------------------------------
# box generators
# --------------------------------------------------------------------------
def dust_flap(d, xa, xb, y0, dirn, dh, relief_a=False, relief_b=False, r=3):
    w = xb - xa
    pts = [(xa, y0), (xb, y0)]
    rad = {}
    if relief_b:
        pts.append((xb - 3, y0 + dirn * dh)); rad[len(pts) - 1] = r
    else:
        pts.append((xb, y0 + dirn * dh * 0.35))
        pts.append((xb - 0.22 * w, y0 + dirn * dh)); rad[len(pts) - 1] = r
    if relief_a:
        pts.append((xa + 3, y0 + dirn * dh)); rad[len(pts) - 1] = r
    else:
        pts.append((xa + 0.22 * w, y0 + dirn * dh)); rad[len(pts) - 1] = r
        pts.append((xa, y0 + dirn * dh * 0.35))
    d.panel(d.rpoly(pts, rad))


def tuck_end_box(d, L, W, H, glue=15, tuck=None, window=None):
    """Reverse tuck end box; girth panels side by side, length L vertical.
    Panels: glue | front(H) | top(W, window) | back(H) | bottom(W)."""
    tuck = tuck or max(15, round(W * 0.2))
    x1, x2, x3, x4 = H, H + W, 2 * H + W, 2 * H + 2 * W
    d.panel(d.rect(0, 0, x4, L))
    d.panel(Polygon([(0, 0), (-glue, glue * 0.7), (-glue, L - glue * 0.7), (0, L)]))
    for x in (0, x1, x2, x3):
        d.crease(x, 0, x, L)
    dh = round(W * 0.42)
    tr = min(8, tuck * 0.45)
    # top end: closure on top panel
    d.panel(d.rect(x1, L, x2, L + H))
    d.panel(d.rpoly([(x1, L + H), (x2, L + H), (x2 - 2, L + H + tuck), (x1 + 2, L + H + tuck)], {2: tr, 3: tr}))
    dust_flap(d, 0, x1, L, +1, dh, relief_b=True)
    dust_flap(d, x2, x3, L, +1, dh, relief_a=True)
    d.crease(0, L, x3, L)
    d.crease(x1, L + H, x2, L + H)
    # bottom end: closure on bottom panel
    d.panel(d.rect(x3, -H, x4, 0))
    d.panel(d.rpoly([(x3, -H), (x4, -H), (x4 - 2, -H - tuck), (x3 + 2, -H - tuck)], {2: tr, 3: tr}))
    dust_flap(d, 0, x1, 0, -1, dh)
    dust_flap(d, x2, x3, 0, -1, dh, relief_b=True)
    d.crease(0, 0, x1, 0)
    d.crease(x2, 0, x4, 0)
    d.crease(x3, -H, x4, -H)
    if window:
        ww, wl, wr = window
        cx, cy = (x1 + x2) / 2, L / 2
        d.cutout(d.rect(cx - ww / 2, cy - wl / 2, cx + ww / 2, cy + wl / 2, wr))
    return x1, x2, x3, x4


def ear(d, xc, dirx, ya, yb, depth, inset_a, inset_b, ch=6):
    s = 1 if yb > ya else -1
    pts = [(xc, ya),
           (xc + dirx * (depth - ch), ya + s * inset_a),
           (xc + dirx * depth, ya + s * (inset_a + ch + 2)),
           (xc + dirx * depth, yb - s * (inset_b + ch + 2)),
           (xc + dirx * (depth - ch), yb - s * inset_b),
           (xc, yb)]
    d.panel(d.rpoly(pts, {1: 2, 2: 2, 3: 2, 4: 2}))


def mailer_box(d, W, D, H, notch=15):
    """Self-locking mailer (roll-end tuck front): double side walls with
    locking tabs, corner ears, hinged lid with side ears and front tuck."""
    lid_d = D + 2
    Lb, Lt = D + H, D + H + lid_d
    tk = round(H * 0.4)
    d.panel(d.rect(0, 0, W, D))                       # base
    d.panel(d.rect(0, -H, W, 0))                      # front wall
    d.panel(d.rect(0, D, W, Lb))                      # back wall
    d.panel(d.rect(0, Lb, W, Lt))                     # lid
    d.panel(d.rpoly([(0, Lt), (W, Lt), (W - 3, Lt + tk), (3, Lt + tk)], {2: 8, 3: 8}))
    d.cutout(d.circle(W / 2, -H, notch))              # thumb notch
    ew = min(D / 2 - 5, round(H * 0.85))
    le = round(H * 0.75)
    inner = H - 5
    tw = min(30, round(D * 0.18))
    for xc, dx in ((0, -1), (W, +1)):
        ear(d, xc, dx, -H, 0, ew, 1.5, 4)             # front-wall ears
        ear(d, xc, dx, D, Lb, ew, 4, 4)               # back-wall ears
        ear(d, xc, dx, Lb, Lt, le, 10, 14, ch=10)     # lid ears
        xo = xc + dx * H                              # side-wall fold
        xe = xo + dx * inner                          # inner wall free edge
        d.panel(d.rect(min(xc, xo), 0, max(xc, xo), D))
        d.panel(Polygon([(xo, 2), (xe, 6), (xe, D - 6), (xo, D - 2)]))
        for yc in (D * 0.25, D * 0.75):
            d.panel(Polygon([(xe, yc - tw / 2), (xe + dx * 8, yc - tw / 2 + 2),
                             (xe + dx * 8, yc + tw / 2 - 2), (xe, yc + tw / 2)]))
            sx = xc - dx * 1.5
            d.cutout(d.rect(min(sx, sx - dx * 3), yc - tw / 2 - 2, max(sx, sx - dx * 3), yc + tw / 2 + 2, 1))
        d.crease(xc, -H, xc, Lt)
        d.crease(xo, 2, xo, D - 2)
    for y in (0, D, Lb, Lt):
        d.crease(0, y, W, y)
    return Lb, Lt


def gable_box(d, W, D, H, S, Hh, glue=15, tuck=20, hole_w=None):
    """Gable pastry box with integrated carry handle.
    Panels: glue | front(W) | side(D) | back(W) | side(D)."""
    a, b, c, e4 = W, W + D, 2 * W + D, 2 * W + 2 * D
    d.panel(d.rect(0, 0, e4, H))
    d.panel(Polygon([(0, 0), (-glue, 10), (-glue, H - 10), (0, H)]))
    for x in (0, a, b, c):
        d.crease(x, 0, x, H)
    d.crease(0, H, e4, H)
    hole_w = hole_w or min(100, round(W * 0.45))
    for x0 in (0, b):                                 # front & back: roof slope + handle
        d.panel(d.rect(x0, H, x0 + W, H + S))
        d.panel(d.rpoly([(x0, H + S), (x0 + W, H + S), (x0 + W - 25, H + S + Hh), (x0 + 25, H + S + Hh)],
                        {2: 10, 3: 10}))
        hy = H + S + Hh * 0.52
        d.cutout(d.rect(x0 + W / 2 - hole_w / 2, hy - 12, x0 + W / 2 + hole_w / 2, hy + 12, 12))
        d.crease(x0, H + S, x0 + W, H + S)
    for x0 in (a, c):                                 # gable ends (bellows fold)
        d.panel(Polygon([(x0, H), (x0 + D, H), (x0 + D - 1.5, H + S), (x0 + 1.5, H + S)]))
        m = x0 + D / 2
        d.crease(x0, H, m, H + S)
        d.crease(x0 + D, H, m, H + S)
        d.crease(m, H, m, H + S)
    # bottom: full panel + tuck from front, dust flaps on sides, flap on back
    d.panel(d.rect(0, -D, W, 0))
    d.panel(d.rpoly([(0, -D), (W, -D), (W - 3, -D - tuck), (3, -D - tuck)], {2: 8, 3: 8}))
    dh = min(70, round(W * 0.35))
    dust_flap(d, a, b, 0, -1, dh, relief_a=True, relief_b=True)
    dust_flap(d, c, e4, 0, -1, dh, relief_a=True)
    bf = round(D * 0.35)
    d.panel(d.rpoly([(b, 0), (c, 0), (c - 3, -bf), (b + 3, -bf)], {2: 6, 3: 6}))
    d.crease(0, 0, e4, 0)
    d.crease(0, -D, W, -D)
    return a, b, c, e4


def insert_tray(d, ox, oy, w, dd, lh, holes, slits=0, part="insert"):
    """Raised insert: platform w x dd with folding legs and cup holes."""
    d.panel(d.rect(ox, oy, ox + w, oy + dd), part)
    d.panel(Polygon([(ox, oy), (ox + w, oy), (ox + w - 2, oy - lh), (ox + 2, oy - lh)]), part)
    d.panel(Polygon([(ox, oy + dd), (ox + w, oy + dd), (ox + w - 2, oy + dd + lh), (ox + 2, oy + dd + lh)]), part)
    d.panel(Polygon([(ox, oy), (ox, oy + dd), (ox - lh, oy + dd - 2), (ox - lh, oy + 2)]), part)
    d.panel(Polygon([(ox + w, oy), (ox + w, oy + dd), (ox + w + lh, oy + dd - 2), (ox + w + lh, oy + 2)]), part)
    for x0, y0, x1, y1 in ((ox, oy, ox + w, oy), (ox, oy + dd, ox + w, oy + dd),
                           (ox, oy, ox, oy + dd), (ox + w, oy, ox + w, oy + dd)):
        d.crease(x0, y0, x1, y1)
    for hx, hy, r in holes:
        d.cutout(d.circle(ox + hx, oy + hy, r), part)
        for k in range(slits):                         # flex slits around the cup
            a = 2 * math.pi * (k + 0.5) / slits
            d.slit(ox + hx + r * math.cos(a), oy + hy + r * math.sin(a),
                   ox + hx + (r + 6) * math.cos(a), oy + hy + (r + 6) * math.sin(a))


# --------------------------------------------------------------------------
# the six L'Adresse boxes
# --------------------------------------------------------------------------
def build():
    dies = []

    d = Die("01_boite-cookies-longue", "Boîte longue cookies à fenêtre",
            "240 × 90 × 55 mm (L × P × H)", "Fermeture à pattes rentrantes inversées, fenêtre 60 × 170 mm")
    x1, x2, x3, x4 = tuck_end_box(d, 240, 90, 55, window=(60, 170, 8))
    d.sweet(27.5, 120, 8.5, rot=90)
    d.logo(172.5, 120, 21, rot=90)
    dies.append(d)

    d = Die("02_boite-carree-24x24x14", "Boîte carrée 24 × 24 × 14 cm",
            "240 × 240 × 140 mm (L × P × H)", "Boîte postale auto-montante, parois doubles verrouillées, couvercle à rabat")
    Lb, Lt = mailer_box(d, 240, 240, 140, notch=15)
    d.logo(120, (Lb + Lt) / 2 - 8, 40, rot=180)
    d.sweet(120, -62, 15, rot=180)
    dies.append(d)

    d = Die("03_boite-gable-patisserie", "Boîte gable pâtisserie avec poignée",
            "220 × 160 × 150 mm (L × P × H corps) + toit/poignée", "Fond à rabat rentrant, poignée à fenêtre 100 × 24 mm")
    a, b, c, e4 = gable_box(d, 220, 160, 150, S=90, Hh=45)
    d.logo(110, 70, 34)
    d.sweet(a + 80, 80, 12)
    d.logo(b + 110, 70, 34)
    dies.append(d)

    d = Die("04_boite-verrines", "Boîte 3 verrines à fenêtre + cale",
            "270 × 110 × 85 mm (L × P × H)", "Fenêtre 76 × 220 mm · cale 266 × 106 mm, 3 alvéoles Ø 72 mm, pieds 40 mm")
    x1, x2, x3, x4 = tuck_end_box(d, 270, 110, 85, window=(76, 220, 10))
    d.sweet(42.5, 135, 11, rot=90)
    d.logo(237.5, 135, 26, rot=90)
    insert_tray(d, x4 + 40 + 40, 60, 266, 106, 40,
                [(133 - 85, 53, 36), (133, 53, 36), (133 + 85, 53, 36)], slits=8)
    dies.append(d)

    d = Die("05_boite-carree-basse-18x18x7.5", "Boîte carrée basse pâtisserie",
            "180 × 180 × 75 mm (L × P × H)", "Boîte postale auto-montante, parois doubles verrouillées, couvercle à rabat")
    Lb, Lt = mailer_box(d, 180, 180, 75, notch=12)
    d.logo(90, (Lb + Lt) / 2 - 6, 30, rot=180)
    d.sweet(90, -34, 9.5, rot=180)
    dies.append(d)

    d = Die("06_porte-gobelets-2-cafes", "Porte-gobelets 2 cafés avec poignée",
            "195 × 95 × 210 mm (L × P × H corps) + toit/poignée",
            "2 fenêtres 72 × 115 mm · cale porte-gobelets 2 × Ø 75 mm, pieds 70 mm")
    a, b, c, e4 = gable_box(d, 195, 95, 210, S=55, Hh=45, hole_w=90)
    for wx in (195 / 2 - 48.75, 195 / 2 + 48.75):
        d.cutout(d.rect(wx - 36, 80, wx + 36, 195, 14))
    d.logo(97.5, 24, 16, tagline=False)
    d.sweet(a + 47.5, 110, 9, rot=90)
    d.logo(b + 97.5, 100, 30)
    insert_tray(d, e4 + 40 + 70, 30, 193, 93, 70,
                [(96.5 - 48, 46.5, 37.5), (96.5 + 48, 46.5, 37.5)], slits=8)
    dies.append(d)
    return dies


# --------------------------------------------------------------------------
# info block (outlined text)
# --------------------------------------------------------------------------
def info_block(d, x0, ytop, width_avail):
    marks, lines = [], []
    fb, fr = Font(F_SANS_B), Font(F_SANS)

    def txt(font, s, size, x, y):
        marks.append(font.outline(s, size, tf_place(x, y), "start"))
        return font.width(s, size)

    y = ytop - 7
    txt(fb, "L’ADRESSE — " + d.title.upper(), 6, x0, y)
    y -= 8
    txt(fr, "Dimensions : " + d.dims + "   ·   Format à plat : %.0f × %.0f mm   ·   Échelle 1:1 (mm)"
        % (d.flat[0], d.flat[1]), 3.6, x0, y)
    y -= 6
    txt(fr, d.notes, 3.6, x0, y)
    y -= 9
    lines.append(("cut", (x0, y + 1.2), (x0 + 20, y + 1.2)))
    w = txt(fr, "DÉCOUPE — trait plein", 3.6, x0 + 24, y)
    xx = x0 + 24 + w + 12
    lines.append(("crease", (xx, y + 1.2), (xx + 20, y + 1.2)))
    w = txt(fr, "RAINAGE / PLI — pointillés", 3.6, xx + 24, y)
    xx = xx + 24 + w + 12
    lines.append(("cut", (xx, y + 1.2), (xx + 100, y + 1.2)))
    lines.append(("cut", (xx, y - 1), (xx, y + 3.4)))
    lines.append(("cut", (xx + 100, y - 1), (xx + 100, y + 3.4)))
    txt(fr, "100 mm (contrôle d’échelle)", 3.0, xx + 30, y + 3)
    y -= 7
    txt(fr, "Calques : DECOUPE · RAINAGE · MARQUAGE (repère visuel, ne pas découper) · INFOS (ne pas découper)",
        3.0, x0, y)
    return marks, lines, y - 3


# --------------------------------------------------------------------------
# writers
# --------------------------------------------------------------------------
def fmt(v): return ("%.3f" % v).rstrip("0").rstrip(".") if abs(v) > 5e-4 else "0"


def svg_d(cmds, T):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append("Z")
            continue
        pts = [T((c[i], c[i + 1])) for i in range(1, len(c), 2)]
        out.append(c[0] + " ".join(fmt(p[0]) + "," + fmt(p[1]) for p in pts))
    return " ".join(out)


def pdf_ops(cmds, T):
    out = []
    for c in cmds:
        if c[0] == "Z":
            out.append("h")
            continue
        pts = [T((c[i], c[i + 1])) for i in range(1, len(c), 2)]
        nums = " ".join(fmt(p[0]) + " " + fmt(p[1]) for p in pts)
        out.append(nums + " " + {"M": "m", "L": "l", "C": "c"}[c[0]])
    return "\n".join(out)


def write_outputs(d, production):
    cuts = d.cut_paths()
    creases = d.merged_creases()
    minx, miny, maxx, maxy = d.bounds
    layers = [("DECOUPE", "cut", cuts), ("RAINAGE", "crease", [[["M", *a], ["L", *b]] for a, b in creases])]
    ibottom = miny
    if not production:
        layers.append(("MARQUAGE", "fill", d.marks))
        imarks, ilines, ibottom = info_block(d, minx, miny - 14, maxx - minx)
        layers.append(("INFOS", "info", (imarks, ilines)))
        maxx = max(maxx, minx + 330)
    ox, oy = minx - MARGIN, ibottom - MARGIN
    Wd, Hd = maxx - minx + 2 * MARGIN, maxy + MARGIN - oy
    suffix = "_production" if production else ""
    base = os.path.join(OUT, d.key + suffix)

    # ---------------- SVG ----------------
    Ts = lambda p: (p[0] - ox, (maxy + MARGIN) - p[1])
    st = 'fill="none" stroke="#000000" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % STROKE
    s = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
         'width="%smm" height="%smm" viewBox="0 0 %s %s">' % (fmt(Wd), fmt(Hd), fmt(Wd), fmt(Hd)),
         '<title>L’Adresse — %s — tracé de découpe 1:1 (mm)</title>' % d.title]
    for name, kind, data in layers:
        s.append('<g id="%s" inkscape:groupmode="layer" inkscape:label="%s">' % (name, name))
        if kind == "cut":
            for p in data:
                s.append('<path %s d="%s"/>' % (st, svg_d(p, Ts)))
        elif kind == "crease":
            for p in data:
                s.append('<path %s stroke-dasharray="%s %s" d="%s"/>' % (st, DASH[0], DASH[1], svg_d(p, Ts)))
        elif kind == "fill":
            for p in data:
                s.append('<path fill="#000000" fill-rule="evenodd" stroke="none" d="%s"/>' % svg_d(p, Ts))
        else:
            marks, lines = data
            for p in marks:
                s.append('<path fill="#000000" fill-rule="evenodd" stroke="none" d="%s"/>' % svg_d(p, Ts))
            for k, a, b in lines:
                extra = ' stroke-dasharray="%s %s"' % DASH if k == "crease" else ""
                s.append('<path %s%s d="%s"/>' % (st, extra, svg_d([["M", *a], ["L", *b]], Ts)))
        s.append("</g>")
    s.append("</svg>")
    with open(base + ".svg", "w", encoding="utf-8") as f:
        f.write("\n".join(s) + "\n")

    # ---------------- PDF (with optional-content layers) ----------------
    K = 72 / 25.4
    Tp = lambda p: (p[0] - ox, p[1] - oy)
    content = ["%.6f 0 0 %.6f 0 0 cm" % (K, K), "1 J 1 j 0 G 0 g %s w" % STROKE]
    for i, (name, kind, data) in enumerate(layers):
        content.append("/OC /L%d BDC q" % i)
        if kind == "cut":
            content.append("[] 0 d")
            content += [pdf_ops(p, Tp) + " S" for p in data]
        elif kind == "crease":
            content.append("[%s %s] 0 d" % DASH)
            content += [pdf_ops(p, Tp) + " S" for p in data]
        elif kind == "fill":
            content += [pdf_ops(p, Tp) + " f*" for p in data]
        else:
            marks, lines = data
            content += [pdf_ops(p, Tp) + " f*" for p in marks]
            for k, a, b in lines:
                content.append(("[%s %s] 0 d " % DASH if k == "crease" else "[] 0 d ")
                               + pdf_ops([["M", *a], ["L", *b]], Tp) + " S")
        content.append("Q EMC")
    stream = zlib.compress("\n".join(content).encode("latin-1"))
    nl = len(layers)
    objs = []
    ocg_ids = [5 + i for i in range(nl)]
    objs.append("<< /Type /Catalog /Pages 2 0 R /OCProperties << /OCGs [%s] /D << /Order [%s] /ON [%s] >> >> >>"
                % tuple([" ".join("%d 0 R" % o for o in ocg_ids)] * 3))
    objs.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.3f %.3f] /Contents 4 0 R "
                "/Resources << /Properties << %s >> >> >>"
                % (Wd * K, Hd * K, " ".join("/L%d %d 0 R" % (i, o) for i, o in enumerate(ocg_ids))))
    objs.append(None)  # stream
    for name, _, _ in layers:
        objs.append("<< /Type /OCG /Name (%s) >>" % name)
    out = bytearray(b"%PDF-1.6\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        if o is None:
            out += b"%d 0 obj\n<< /Length %d /Filter /FlateDecode >>\nstream\n" % (i, len(stream))
            out += stream + b"\nendstream\nendobj\n"
        else:
            out += ("%d 0 obj\n%s\nendobj\n" % (i, o)).encode("latin-1")
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info << /Title (L'Adresse - %s) /Producer (generate_dielines.py) >> >>\n" \
           % (len(objs) + 1, d.key.encode())
    out += b"startxref\n%d\n%%%%EOF\n" % xref
    with open(base + ".pdf", "wb") as f:
        f.write(out)
    return len(cuts), len(creases)


def main():
    for d in build():
        d.bounds = d.validate()
        main_shape = d.shapes()[0].bounds
        d.flat = (main_shape[2] - main_shape[0], main_shape[3] - main_shape[1])
        for prod in (False, True):
            nc, ncr = write_outputs(d, prod)
        print("%-34s flat %4.0f x %4.0f mm  cut paths %3d  crease lines %3d"
              % (d.key, d.flat[0], d.flat[1], nc, ncr))


if __name__ == "__main__":
    main()
