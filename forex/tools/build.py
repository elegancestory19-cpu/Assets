"""Forex (PVC foam) production files for Elegance Story: wayfinding signs + photo frames.
Sheet 2440×1220 mm → 5 plates 600×900 mm (the UV flatbed's bed). For each plate:
  out/plate_N_print.pdf   vector print file (artwork with 2 mm bleed + registration crosses), 1:1 in mm
  out/plate_N_cut.dxf     CNC router cut paths (closed polylines, mm, origin = plate's lower-left corner) + REG layer
  out/plate_N_cut.svg     the same cut paths (CutContour, for print-and-cut software)
  out/plate_N_preview.png preview with cut lines
  out/sheet_plan.pdf/.dxf how to cut the 2440×1220 sheet into the 5 plates
Arabic is shaped with HarfBuzz and converted to outlines, so the files need no fonts.
Run: <venv>/bin/python tools/build.py   (needs uharfbuzz fonttools cairosvg ezdxf pillow)
"""
import base64, io, math, os, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import cairosvg, ezdxf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
FONT = os.path.join(REPO, 'es-keynote', 'fonts', 'Cairo.ttf')
IMGS = os.path.join(REPO, 'source', 'images')
PW, PH, BLEED, GAP_MIN = 600, 900, 2.0, 10.0

# ───────────── text → outlines (HarfBuzz shaping, works for Arabic RTL and Latin)
_F = {}
def _font(wght):
    if wght not in _F:
        data = open(FONT, 'rb').read()
        face = hb.Face(data); f = hb.Font(face); f.set_variations({'wght': wght})
        tt = TTFont(FONT); st = instantiateVariableFont(tt, {'wght': wght, 'slnt': 0})
        _F[wght] = (f, st, st['head'].unitsPerEm)
    return _F[wght]
def text_path(s, size, x, y, wght=800, anchor='middle', rtl=None):
    """size = cap/em size in mm. (x, y) = baseline anchor. Returns (svg path d, width_mm)."""
    f, tt, upem = _font(wght)
    buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(f, buf, {})
    k = size / upem; gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    adv = sum(p.x_advance for p in buf.glyph_positions) * k
    x0 = x - adv / 2 if anchor == 'middle' else (x - adv if anchor == 'end' else x)
    pen = SVGPathPen(gs); cx = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        tp = TransformPen(pen, (k, 0, 0, -k, x0 + (cx + pos.x_offset) * k, y - pos.y_offset * k))
        gs[name].draw(tp); cx += pos.x_advance
    return pen.getCommands(), adv
def T(s, size, x, y, fill, wght=800, anchor='middle', maxw=None):
    d, w = text_path(s, size, x, y, wght, anchor)
    if maxw and w > maxw:
        size *= maxw / w; d, w = text_path(s, size, x, y, wght, anchor)
    return f'<path d="{d}" fill="{fill}"/>'

def TR(parts, size, x, y, fill, wght=800):
    """mixed Arabic + numbers: parts in reading order (right to left); each part is shaped on its own, then
    laid out from the right, so numbers keep their left-to-right order"""
    ws = [text_path(p, size, 0, 0, wght, 'start')[1] for p in parts]; gap = size * .28
    total = sum(ws) + gap * (len(parts) - 1); cx = x + total / 2; out = []
    for p, w in zip(parts, ws):
        cx -= w; out.append(T(p, size, cx, y, fill, wght, 'start')); cx -= gap
    return ''.join(out)

# ───────────── geometry (every cut shape is a closed polygon in mm)
def round_poly(verts, r, n=10):
    pts = []; N = len(verts)
    for i in range(N):
        p0, p1, p2 = verts[i - 1], verts[i], verts[(i + 1) % N]
        a = math.atan2(p0[1] - p1[1], p0[0] - p1[0]); b = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        th = (b - a) % (2 * math.pi); half = th / 2 if th < math.pi else (2 * math.pi - th) / 2
        d = r / math.tan(half) if half > 1e-6 else 0
        u0 = (math.cos(a), math.sin(a)); u2 = (math.cos(b), math.sin(b))
        s0 = (p1[0] + u0[0] * d, p1[1] + u0[1] * d); s2 = (p1[0] + u2[0] * d, p1[1] + u2[1] * d)
        bis = (u0[0] + u2[0], u0[1] + u2[1]); L = math.hypot(*bis) or 1; cd = r / math.sin(half) if half > 1e-6 else 0
        c = (p1[0] + bis[0] / L * cd, p1[1] + bis[1] / L * cd)
        a0 = math.atan2(s0[1] - c[1], s0[0] - c[0]); a2 = math.atan2(s2[1] - c[1], s2[0] - c[0])
        da = (a2 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(n + 1): t = a0 + da * j / n; pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return pts
def rrect(x, y, w, h, r): return round_poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], r)
def circle(cx, cy, r, n=120): return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
def ngon(cx, cy, R, k, rot, r): return round_poly([(cx + R * math.cos(rot + 2 * math.pi * i / k), cy + R * math.sin(rot + 2 * math.pi * i / k)) for i in range(k)], r)
def arch(x, y, w, h, n=60):    # flat bottom, semicircular top
    r = w / 2; pts = [(x, y + h), (x, y + r)]
    pts += [(x + r - r * math.cos(math.pi * i / n), y + r - r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    pts += [(x + w, y + h)]; return round_poly(pts[::1], 0.01, 1) if False else pts
def heart(cx, cy, w, h, n=240):
    raw = []
    for i in range(n):
        t = 2 * math.pi * i / n
        raw.append((16 * math.sin(t) ** 3, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))))
    x0, y0, x1, y1 = bbox(raw)
    return [(cx + (x - (x0 + x1) / 2) / (x1 - x0) * w, cy + (y - (y0 + y1) / 2) / (y1 - y0) * h) for x, y in raw]
def pointer(x, y, w, h, tip, right=True, r=8):
    v = [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h)] if right else [(x + tip, y), (x + w, y), (x + w, y + h), (x + tip, y + h), (x, y + h / 2)]
    return round_poly(v, r)
def offset(pts, d):
    """grow a closed polygon by d (vertex-normal offset; used for the bleed)"""
    pts = [p for i, p in enumerate(pts) if math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) > 1e-3]
    n = len(pts); out = []; area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)); sgn = 1 if area > 0 else -1
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1]); e2 = (p2[0] - p1[0], p2[1] - p1[1])
        n1 = (e1[1], -e1[0]); n2 = (e2[1], -e2[0]); l1 = math.hypot(*n1) or 1; l2 = math.hypot(*n2) or 1
        nx, ny = n1[0] / l1 + n2[0] / l2, n1[1] / l1 + n2[1] / l2; L = math.hypot(nx, ny) or 1
        cosh = max(.35, (nx / L) * (n1[0] / l1) + (ny / L) * (n1[1] / l1))
        out.append((p1[0] + sgn * nx / L * d / cosh, p1[1] + sgn * ny / L * d / cosh))
    return out
def bbox(pts): xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; return min(xs), min(ys), max(xs), max(ys)
def dpath(pts): return 'M' + ' L'.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z'

# ───────────── pictograms (original, drawn in a 100×100 box; fill colour c)
def pic(name, c, x, y, s, bg='none'):
    k = s / 100; g = [f'<g transform="translate({x:.3f},{y:.3f}) scale({k:.5f})" fill="{c}" stroke="none">']
    A = g.append
    def person(cx, top, dress=False):
        A(f'<circle cx="{cx}" cy="{top + 9}" r="9"/>')
        if dress:
            A(f'<path d="M{cx - 11},{top + 22} L{cx + 11},{top + 22} L{cx + 19},{top + 58} L{cx - 19},{top + 58} Z"/>')
            A(f'<rect x="{cx - 9}" y="{top + 56}" width="7" height="27" rx="3.5"/><rect x="{cx + 2}" y="{top + 56}" width="7" height="27" rx="3.5"/>')
        else:
            A(f'<rect x="{cx - 13}" y="{top + 22}" width="26" height="34" rx="6"/>')
            A(f'<rect x="{cx - 12}" y="{top + 50}" width="10" height="33" rx="5"/><rect x="{cx + 2}" y="{top + 50}" width="10" height="33" rx="5"/>')
        A(f'<rect x="{cx - 22}" y="{top + 23}" width="8" height="30" rx="4"/><rect x="{cx + 14}" y="{top + 23}" width="8" height="30" rx="4"/>')
    if name == 'man': person(50, 8)
    elif name == 'woman': person(50, 8, True)
    elif name == 'accessible':
        A('<circle cx="44" cy="14" r="9"/>')
        A('<path d="M38,26 h12 v24 h20 l9,30 h-10 l-7,-22 h-24 z"/>')
        A(f'<path d="M30,44 a26,26 0 1,0 38,30 l-8,-3 a17,17 0 1,1 -24,-18 z"/>')
    elif name == 'prayer':
        A('<path d="M50,4 a9,9 0 1,0 6,15 a7,7 0 1,1 -6,-15 z"/>')
        A('<path fill-rule="evenodd" d="M18,96 V54 Q18,30 50,22 Q82,30 82,54 V96 Z M30,96 V56 Q30,40 50,34 Q70,40 70,56 V96 Z"/>')
        A('<rect x="12" y="90" width="76" height="7" rx="3"/>')
    elif name == 'reception':
        A('<path d="M14,74 a36,36 0 0,1 72,0 z"/><rect x="8" y="78" width="84" height="9" rx="4"/><rect x="45" y="27" width="10" height="9" rx="3"/><rect x="38" y="22" width="24" height="6" rx="3"/>')
    elif name == 'office':
        A('<path fill-rule="evenodd" d="M36,24 h28 a6,6 0 0,1 6,6 v6 h-8 v-4 h-24 v4 h-8 v-6 a6,6 0 0,1 6,-6 z"/>')
        A('<rect x="10" y="38" width="80" height="50" rx="8"/>'); A(f'<rect x="10" y="56" width="80" height="4" fill="{bg}"/><rect x="44" y="52" width="12" height="12" rx="2" fill="{bg}"/>')
    elif name == 'meeting':
        A('<ellipse cx="50" cy="66" rx="40" ry="13"/>'); [A(f'<circle cx="{cx}" cy="{cy}" r="8"/>') for cx, cy in [(22, 36), (50, 28), (78, 36)]]
        [A(f'<path d="M{cx - 10},{cy + 22} a10,10 0 0,1 20,0 z"/>') for cx, cy in [(22, 36), (50, 28), (78, 36)]]
    elif name == 'kitchen':
        A('<path d="M18,40 h56 v26 a22,22 0 0,1 -22,22 h-12 a22,22 0 0,1 -22,-22 z"/>')
        A('<path fill-rule="evenodd" d="M72,46 h6 a12,12 0 0,1 0,24 h-6 v-7 h6 a5,5 0 0,0 0,-10 h-6 z"/>'); A('<rect x="12" y="90" width="70" height="6" rx="3"/>')
        for xx in (32, 46, 60): A(f'<path d="M{xx},34 q-6,-7 0,-14 q6,-7 0,-14" fill="none" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>')
    elif name == 'stairs':
        A('<path d="M8,92 V76 H28 V60 H48 V44 H68 V28 H92 V92 Z"/>'); A('<circle cx="40" cy="14" r="7"/>')
        A('<path d="M33,26 l12,0 l6,14 l-5,2 l-5,-9 l-3,10 l7,10 l-5,3 l-9,-12 z"/>')
    elif name == 'elevator':
        A(f'<rect x="12" y="6" width="76" height="88" rx="10"/>')
        A(f'<path d="M50,18 l16,20 h-32 z" fill="{bg}"/><path d="M50,82 l16,-20 h-32 z" fill="{bg}"/>')
    elif name == 'wifi':
        for r in (42, 29, 16): A(f'<path d="M{50 - r * .8},{74 - r * .6} A{r},{r} 0 0,1 {50 + r * .8},{74 - r * .6}" fill="none" stroke="{c}" stroke-width="8" stroke-linecap="round"/>')
        A('<circle cx="50" cy="78" r="7"/>')
    elif name == 'parking':
        g.append('</g>'); g2 = ''.join(g)
        return g2 + T('P', 80 * k * 1.25, x + 50 * k, y + 88 * k, c, 800)
    elif name == 'cctv':
        A('<path d="M14,30 l58,-10 a5,5 0 0,1 6,4 l3,16 a5,5 0 0,1 -4,6 l-58,10 z"/><rect x="40" y="52" width="8" height="18"/><rect x="18" y="68" width="40" height="8" rx="3"/>')
        A('<circle cx="74" cy="34" r="4" fill="' + bg + '"/>')
    elif name == 'fire':
        A('<rect x="34" y="28" width="30" height="66" rx="12"/><rect x="40" y="16" width="18" height="14" rx="3"/><path d="M58,18 h18 l6,8 h-6 l-4,-4 h-14 z"/>')
        A(f'<path d="M36,30 q-18,8 -16,38" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>')
    elif name == 'firstaid':
        A('<path d="M38,10 h24 v28 h28 v24 h-28 v28 h-24 v-28 h-28 v-24 h28 z"/>')
    elif name == 'nosmoking':
        A('<rect x="16" y="52" width="58" height="12" rx="2"/><rect x="76" y="52" width="9" height="12" rx="2"/>')
        A(f'<path d="M70,46 q-6,-8 0,-16 q6,-8 0,-16" fill="none" stroke="{c}" stroke-width="4.5" stroke-linecap="round"/>')
    elif name == 'wetfloor':
        A('<path d="M50,10 q-22,30 -22,46 a22,22 0 0,0 44,0 q0,-16 -22,-46 z"/>')
        for i in range(3): A(f'<path d="M{14},{82 + i * 0},{0}" />') if False else None
        A(f'<path d="M8,88 q10,-8 21,0 t21,0 t21,0 t21,0" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round"/>')
    elif name == 'exit':
        A(f'<path fill-rule="evenodd" d="M60,6 h32 v88 h-32 z M66,12 v76 h20 v-76 z"/>')
        A('<circle cx="40" cy="14" r="8"/>')
        A(f'<path d="M24,36 L38,26 L52,40 L62,40 M38,26 L32,54 L44,66 L42,90 M32,54 L18,70 L6,70 M24,36 L14,48" fill="none" stroke="{c}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
    g.append('</g>'); return ''.join(g)
def arrow(x, y, s, c, right=True):   # a solid arrow in a s×s box
    k = s / 100; d = 'M10,40 H55 V18 L92,50 L55,82 V60 H10 Z' if right else 'M90,40 H45 V18 L8,50 L45,82 V60 H90 Z'
    return f'<path transform="translate({x:.3f},{y:.3f}) scale({k:.5f})" d="{d}" fill="{c}"/>'

# ───────────── colours
INK, WHITE, CYAN = '#23262E', '#FFFFFF', '#1CCEE9'
RED, GREEN, YEL, BLK = '#D7262A', '#00965E', '#F7C600', '#111111'
GRAD = ['#1CCEE9', '#2457D6', '#8844C0', '#DA43AE', '#E57E22', '#F7C947']

# ───────────── items: (cut polygon, print svg)
def clip(pid, pts): return f'<clipPath id="{pid}"><path d="{dpath(pts)}"/></clipPath>'
_N = [0]
def uid(p='c'): _N[0] += 1; return f'{p}{_N[0]}'
def info_sign(x, y, s, name, ar, fr):
    cut = rrect(x, y, s, s, 12); bl = offset(cut, BLEED); cid = uid()
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{INK}"/>']
    svg.append(f'<rect x="{x}" y="{y + s - 9}" width="{s}" height="9" fill="{CYAN}"/>')
    svg.append(pic(name, WHITE, x + s * .25, y + s * .09, s * .5, INK))
    svg.append(T(ar, s * .115, x + s / 2, y + s * .77, WHITE, 800, maxw=s * .84))
    svg.append(T(fr, s * .07, x + s / 2, y + s * .87, '#C9CED8', 600, maxw=s * .84))
    svg.append('</g>'); return cut, ''.join(svg)
def round_sign(cx, cy, r, name, kind, ar, fr):
    cut = circle(cx, cy, r); bl = offset(cut, BLEED); cid = uid(); s = r * 2
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{WHITE}"/>']
    if kind == 'prohibit':
        rr, oy = r * .55, cy - r * .2
        svg.append(pic(name, BLK, cx - rr * .72, oy - rr * .72, rr * 1.44, WHITE))
        svg.append(f'<circle cx="{cx}" cy="{oy}" r="{rr}" fill="none" stroke="{RED}" stroke-width="{r * .09:.2f}"/>')
        a = math.radians(45); svg.append(f'<line x1="{cx - rr * math.cos(a):.2f}" y1="{oy - rr * math.sin(a):.2f}" x2="{cx + rr * math.cos(a):.2f}" y2="{oy + rr * math.sin(a):.2f}" stroke="{RED}" stroke-width="{r * .09:.2f}"/>')
    else:
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 3}" fill="{INK}"/>'); svg.append(pic(name, WHITE, cx - r * .42, cy - r * .7, r * .84, INK))
    col = BLK if kind == 'prohibit' else WHITE
    ty = cy + (r * .6 if kind == 'prohibit' else r * .58)
    svg.append(T(ar, r * .17, cx, ty, RED if kind == 'prohibit' else WHITE, 800, maxw=r * 1.4))
    svg.append(T(fr, r * .1, cx, ty + r * .17, col if kind != 'prohibit' else '#444', 600, maxw=r * 1.1))
    svg.append('</g>'); return cut, ''.join(svg)
def safety_square(x, y, s, name, col, ar, fr):
    cut = rrect(x, y, s, s, 12); bl = offset(cut, BLEED); cid = uid()
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{col}"/>', pic(name, WHITE, x + s * .25, y + s * .08, s * .5, col),
           T(ar, s * .12, x + s / 2, y + s * .76, WHITE, 800, maxw=s * .86), T(fr, s * .075, x + s / 2, y + s * .88, WHITE, 600, maxw=s * .86), '</g>']
    return cut, ''.join(svg)
def warning_tri(x, y, side, name, ar, fr):
    h = side * math.sqrt(3) / 2; cut = round_poly([(x + side / 2, y), (x + side, y + h), (x, y + h)], 14); bl = offset(cut, BLEED); cid = uid()
    inner = round_poly([(x + side / 2, y + 22), (x + side - 19, y + h - 11), (x + 19, y + h - 11)], 8)
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{BLK}"/><path d="{dpath(inner)}" fill="{YEL}"/>',
           pic(name, BLK, x + side / 2 - side * .17, y + h * .3, side * .34, YEL),
           T(ar, side * .075, x + side / 2, y + h * .8, BLK, 800, maxw=side * .5), T(fr, side * .048, x + side / 2, y + h * .87, BLK, 700, maxw=side * .42), '</g>']
    return cut, ''.join(svg)
def exit_sign(x, y, w, h, ar, fr, right=True):
    cut = rrect(x, y, w, h, 12); bl = offset(cut, BLEED); cid = uid()
    px = x + 14 if right else x + w - 14 - h * .72
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{GREEN}"/>', pic('exit', WHITE, px, y + h * .14, h * .72, GREEN),
           arrow(x + w - 14 - h * .5 if right else x + 14, y + h * .25, h * .5, WHITE, right)]
    ax = x + w - 14 - h * .5 if right else x + 14
    L0, L1 = (px + h * .72, ax) if right else (ax + h * .5, px)
    tx, gw = (L0 + L1) / 2, (L1 - L0) * .88
    svg += [T(ar, h * .26, tx, y + h * .52, WHITE, 800, maxw=gw), T(fr, h * .15, tx, y + h * .78, WHITE, 700, maxw=gw), '</g>']
    return cut, ''.join(svg)
def dir_sign(x, y, w, h, name, ar, fr, right=True):
    tip = h * .45; cut = pointer(x, y, w, h, tip, right, 8); bl = offset(cut, BLEED); cid = uid()
    ix = x + 14 if right else x + w - 14 - h * .64
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{INK}"/>', pic(name, WHITE, ix, y + h * .18, h * .64, INK)]
    tx = (x + h * .75 + (x + w - tip)) / 2 if right else (x + tip + (x + w - h * .75)) / 2
    svg += [T(ar, h * .27, tx, y + h * .5, WHITE, 800, maxw=w * .5), T(fr, h * .16, tx, y + h * .78, '#C9CED8', 600, maxw=w * .5)]
    svg.append(f'<path d="{dpath(pointer(x + 5, y + 5, w - 10, h - 10, tip - 4, right, 5))}" fill="none" stroke="{CYAN}" stroke-width="1.6"/></g>')
    return cut, ''.join(svg)
def name_plate(x, y, w, h, ar, fr):
    cut = rrect(x, y, w, h, 8); bl = offset(cut, BLEED); cid = uid()
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{INK}"/><rect x="{x + w - 8}" y="{y - 3}" width="11" height="{h + 6}" fill="{CYAN}"/>',
           T(ar, h * .34, x + (w - 8) / 2, y + h * .5, WHITE, 800, maxw=w * .84), T(fr, h * .2, x + (w - 8) / 2, y + h * .8, '#C9CED8', 600, maxw=w * .84), '</g>']
    return cut, ''.join(svg)
_IMG = {}
def img_href(n):
    if n not in _IMG:
        im = Image.open(os.path.join(IMGS, f'{n:02d}.jpg')).convert('RGB'); b = io.BytesIO(); im.save(b, 'JPEG', quality=92)
        _IMG[n] = 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    return _IMG[n]
def scale_poly(pts, k):
    x0, y0, x1, y1 = bbox(pts); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]
def photo_frame(cut, n, border=14, scaled=False):
    """the photo fills the shape; a printed frame border (ink) with a thin brand-gradient line inside it"""
    bl = offset(cut, BLEED); x0, y0, x1, y1 = bbox(cut); w, h = x1 - x0, y1 - y0; cid, gid, iid = uid(), uid('g'), uid('i')
    if scaled:   # shapes with a cusp (the heart): shrink instead of offsetting, so the inner lines never cross
        x0_, y0_, x1_, y1_ = bbox(cut); W_ = x1_ - x0_
        inner = scale_poly(cut, 1 - 2 * border / W_); line = scale_poly(cut, 1 - 2 * (border - 2.5) / W_)
    else:
        inner = offset(cut, -border); line = offset(cut, -border + 2.5)
    s = max(w, h) * 1.02
    stops = ''.join(f'<stop offset="{i / (len(GRAD) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(GRAD))
    svg = [f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient>', clip(cid, bl), clip(iid, inner),
           f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{INK}"/></g>',
           f'<path d="{dpath(line)}" fill="none" stroke="url(#{gid})" stroke-width="2.2"/>',
           f'<g clip-path="url(#{iid})"><image href="{img_href(n)}" x="{(x0 + x1) / 2 - s / 2:.3f}" y="{(y0 + y1) / 2 - s / 2:.3f}" width="{s:.3f}" height="{s:.3f}" preserveAspectRatio="xMidYMid slice"/></g>']
    return cut, ''.join(svg)
def stand(x, y, w=60, h=160):   # easel back-leg, glued behind a frame; the angled foot sets ~15°
    cut = round_poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h - math.tan(math.radians(15)) * w)], 3)
    return cut, f'<path d="{dpath(offset(cut, BLEED))}" fill="{INK}"/>'

# ───────────── the 5 plates (positions in mm, origin top-left of the plate)
def plate1():
    S = 180; names = [('man', 'رجال', 'Hommes'), ('woman', 'نساء', 'Femmes'), ('accessible', 'ذوي الاحتياجات الخاصة', 'PMR'),
                      ('prayer', 'مصلى', 'Salle de prière'), ('reception', 'الاستقبال', 'Accueil'), ('office', 'مكتب', 'Bureau'),
                      ('meeting', 'قاعة الاجتماعات', 'Salle de réunion'), ('kitchen', 'مطبخ', 'Cuisine'), ('stairs', 'درج', 'Escalier'),
                      ('elevator', 'مصعد', 'Ascenseur'), ('wifi', 'واي فاي مجاني', 'Wi-Fi gratuit'), ('parking', 'موقف السيارات', 'Parking')]
    return [info_sign(15 + (i % 3) * (S + 15), 36 + (i // 3) * (S + 36), S, *names[i]) for i in range(12)]
def plate2():
    it = [round_sign(15 + 95, 25 + 95, 95, 'nosmoking', 'prohibit', 'ممنوع التدخين', 'Défense de fumer'),
          round_sign(15 + 190 + 15 + 95, 25 + 95, 95, 'cctv', 'info', 'منطقة مراقبة', 'Vidéosurveillance'),
          safety_square(430, 35, 160, 'fire', RED, 'طفاية حريق', 'Extincteur'),
          warning_tri(15, 240, 230, 'wetfloor', 'أرضية مبللة', 'Sol glissant'),
          safety_square(270, 250, 160, 'firstaid', GREEN, 'إسعافات أولية', 'Premiers secours'),
          exit_sign(12, 470, 283, 140, 'مخرج', 'Sortie', True), exit_sign(305, 470, 283, 140, 'مخرج نجدة', 'Sortie de secours', False),
          dir_sign(12, 640, 283, 100, 'man', 'مراحيض', 'Toilettes', True), dir_sign(305, 640, 283, 100, 'reception', 'الاستقبال', 'Accueil', False),
          dir_sign(12, 770, 283, 100, 'prayer', 'مصلى', 'Salle de prière', True), dir_sign(305, 770, 283, 100, 'exit', 'مخرج', 'Sortie', False)]
    it += [stand(450 + i * 70, 222) for i in range(2)]
    return it
def plate3():
    return [photo_frame(arch(20, 14, 265, 345), 1), photo_frame(arch(315, 14, 265, 345), 2),
            photo_frame(circle(152, 505, 130), 3), photo_frame(circle(448, 505, 130), 4),
            photo_frame(heart(152, 758, 262, 240), 5, scaled=True), photo_frame(heart(448, 758, 262, 240), 6, scaled=True)]
def plate4():
    return [photo_frame(rrect(14, 14, 300, 420, 10), 7), photo_frame(ngon(458, 140, 122, 6, math.pi / 6, 8), 8),
            photo_frame(rrect(330, 272, 256, 256, 22), 9),
            photo_frame(rrect(14, 452, 300, 210, 10), 10), photo_frame(rrect(14, 678, 300, 210, 10), 11),
            photo_frame(round_poly([(330, 545), (586, 545), (586, 888), (330, 888)], 128) if False else arch(330, 545, 256, 343), 12)]
def plate5():
    names = [('مكتب المدير', 'Direction'), ('المحاسبة', 'Comptabilité'), ('قاعة الانتظار', "Salle d'attente"),
             ('الأمانة', 'Secrétariat'), ('خاص', 'Privé'), ('الأرشيف', 'Archives')]
    it = [name_plate(14 + (i % 2) * 292, 16 + (i // 2) * 98, 280, 82, *names[i]) for i in range(6)]
    it += [stand(16 + i * 72, 330 + r * 185) for r in range(3) for i in range(8)]
    return it
def mini_sign(x, y, s, kind, ar, fr):
    cut = rrect(x, y, s, s, 10); bl = offset(cut, BLEED); cid = uid(); cx = x + s / 2; iy = y + s * .3
    svg = [clip(cid, bl), f'<g clip-path="url(#{cid})"><path d="{dpath(bl)}" fill="{INK}"/><rect x="{x}" y="{y + s - 7}" width="{s}" height="7" fill="{CYAN}"/>']
    if kind in ('push', 'pull'): svg.append(arrow(cx - s * .2, iy - s * .2, s * .4, WHITE, kind == 'push'))
    elif kind == 'open': svg.append(f'<circle cx="{cx}" cy="{iy}" r="{s * .13}" fill="#2BD47A"/>')
    elif kind == 'closed': svg.append(f'<circle cx="{cx}" cy="{iy}" r="{s * .13}" fill="{RED}"/>')
    elif kind == 'noentry': svg += [f'<circle cx="{cx}" cy="{iy}" r="{s * .16}" fill="{RED}"/>', f'<rect x="{cx - s * .1}" y="{iy - s * .03}" width="{s * .2}" height="{s * .06}" rx="2" fill="{WHITE}"/>']
    elif kind == 'step': svg += [f'<path d="{dpath(round_poly([(cx, iy - s * .16), (cx + s * .18, iy + s * .15), (cx - s * .18, iy + s * .15)], 4))}" fill="{YEL}"/>', T('!', s * .2, cx, iy + s * .12, BLK, 800)]
    elif kind == 'cash': svg += [f'<rect x="{cx - s * .17}" y="{iy - s * .1}" width="{s * .34}" height="{s * .2}" rx="3" fill="{WHITE}"/>', f'<circle cx="{cx}" cy="{iy}" r="{s * .05}" fill="{INK}"/>']
    elif kind == 'thanks': svg.append(f'<path d="{dpath(heart(cx, iy, s * .3, s * .27))}" fill="#DA43AE"/>')
    svg += [T(ar, s * .14, cx, y + s * .69, WHITE, 800, maxw=s * .86), T(fr, s * .085, cx, y + s * .83, '#C9CED8', 600, maxw=s * .86), '</g>']
    return cut, ''.join(svg)
def plate6():   # 600×300, from the last offcut of the sheet
    S, g = 130, (600 - 4 * 130) / 5
    signs = [('push', 'ادفع', 'Poussez'), ('pull', 'اسحب', 'Tirez'), ('open', 'مفتوح', 'Ouvert'), ('closed', 'مغلق', 'Fermé'),
             ('noentry', 'ممنوع الدخول', 'Accès interdit'), ('step', 'انتبه للدرجة', 'Attention à la marche'), ('cash', 'الدفع هنا', 'Caisse'), ('thanks', 'شكراً لزيارتكم', 'Merci de votre visite')]
    return [mini_sign(g + (i % 4) * (S + g), 13 + (i // 4) * (S + 14), S, *signs[i]) for i in range(8)]
PLATES = [('1', 'لافتات الأبواب (12)', plate1), ('2', 'السلامة والاتجاهات (11 + 2 حوامل)', plate2), ('3', 'إطارات الصور 1-6', plate3),
          ('4', 'إطارات الصور 7-12', plate4), ('5', 'لوحات المكاتب (6) + 24 حامل', plate5), ('6', 'لافتات صغيرة للأبواب (8) من البقية', plate6)]
SIZE = {'6': (600, 300)}

# ───────────── checks + writers
def check(items, name):
    boxes = [bbox(offset(c, BLEED)) for c, _ in items]
    for i, (a, b, c, d) in enumerate(boxes):
        if a < 4 or b < 4 or c > PW - 4 or d > PH - 4: sys.exit(f'plate {name}: item {i} out of the safe area {a:.1f},{b:.1f},{c:.1f},{d:.1f}')
    cuts = [bbox(c) for c, _ in items]
    for i in range(len(cuts)):
        for j in range(i + 1, len(cuts)):
            A, B = cuts[i], cuts[j]
            gx = max(B[0] - A[2], A[0] - B[2]); gy = max(B[1] - A[3], A[1] - B[3])
            if max(gx, gy) < GAP_MIN and not (name == '3' and max(gx, gy) > 2):
                # bounding boxes may touch for curved shapes; check true polygon distance coarsely
                da = min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in items[i][0][::3] for q in items[j][0][::3])
                if da < GAP_MIN: sys.exit(f'plate {name}: items {i} and {j} are only {da:.1f} mm apart (need ≥ {GAP_MIN})')
def REGS(): return [(8, 8), (PW - 8, 8), (8, PH - 8), (PW - 8, PH - 8)]
def reg_svg(): return ''.join(f'<path d="M{x - 5},{y} H{x + 5} M{x},{y - 5} V{y + 5}" stroke="#000" stroke-width=".3"/><circle cx="{x}" cy="{y}" r="2.5" fill="none" stroke="#000" stroke-width=".3"/>' for x, y in REGS())
def write_plate(pid, title, items):
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}">'
    art = ''.join(s for _, s in items)
    cuts = ''.join(f'<path d="{dpath(c)}" fill="none" stroke="#EC008C" stroke-width=".25"/>' for c, _ in items)
    cairosvg.svg2pdf(bytestring=(head + art + reg_svg() + '</svg>').encode(), write_to=os.path.join(OUT, f'plate_{pid}_print.pdf'))
    open(os.path.join(OUT, f'plate_{pid}_cut.svg'), 'w').write(head + '<g id="CutContour">' + cuts + '</g><g id="REG">' + reg_svg() + '</g></svg>')
    prev = head + f'<rect width="{PW}" height="{PH}" fill="#f4f4f2"/>' + art + cuts + reg_svg() + '</svg>'
    cairosvg.svg2png(bytestring=prev.encode(), write_to=os.path.join(OUT, f'plate_{pid}_preview.png'), output_width=900)
    doc = ezdxf.new('R2010', setup=False); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    doc.layers.add('CUT', color=6); doc.layers.add('REG', color=7)
    for c, _ in items: msp.add_lwpolyline([(x, PH - y) for x, y in c], close=True, dxfattribs={'layer': 'CUT'})
    msp.add_lwpolyline([(0, 0), (PW, 0), (PW, PH), (0, PH)], close=True, dxfattribs={'layer': 'REG'})
    for x, y in REGS(): msp.add_circle((x, PH - y), 2.5, dxfattribs={'layer': 'REG'})
    doc.saveas(os.path.join(OUT, f'plate_{pid}_cut.dxf'))
    print(f'plate {pid}: {len(items)} pieces · {title}')
def write_sheet_plan():
    SW, SH, K = 2440, 1220, 4   # 4 mm saw kerf
    rects = [(0, 0, 900, 600), (0, 600 + K, 900, 600), (900 + K, 0, 900, 600), (900 + K, 600 + K, 900, 600), (1800 + 2 * K, 0, 600, 900), (1800 + 2 * K, 900 + K, 600, 300)]
    w = 1800
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}px" height="{w * (SH + 160) / (SW + 80):.0f}px" viewBox="-40 -60 {SW + 80} {SH + 160}">'
    body = [f'<rect x="-40" y="-60" width="{SW + 80}" height="{SH + 160}" fill="#fff"/>', f'<rect x="0" y="0" width="{SW}" height="{SH}" fill="#fff" stroke="#000" stroke-width="3"/>']
    for i, (x, y, rw, rh) in enumerate(rects):
        body.append(f'<rect x="{x}" y="{y}" width="{rw}" height="{rh}" fill="#e8f9fc" stroke="#1CCEE9" stroke-width="3"/>')
        big = rh > 400
        body.append(T(f'{i + 1}', 120 if big else 80, x + rw / 2, y + rh / 2 + (20 if big else 0), '#23262E', 800))
        body.append(T(f'{rw} × {rh} mm', 48 if big else 38, x + rw / 2, y + rh / 2 + (90 if big else 60), '#555', 600))
    used = sum(rw * rh for _, _, rw, rh in rects) / (SW * SH) * 100
    body.append(TR(['المستعمل:', f'{used:.1f}%', 'من اللوح · الباقي غير خطوط المنشار والحواف'], 40, SW / 2, SH + 70, '#23262E', 700))
    print(f'sheet use: {used:.1f}%')
    body.append(TR(['لوح فوركس', '2440 × 1220 mm', ':', '5', 'قطع', '600 × 900 mm', '+', '1', 'قطعة', '600 × 300 mm'], 52, SW / 2, -14, '#23262E', 800))
    svg = head + ''.join(body) + '</svg>'
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(OUT, 'sheet_plan.pdf')); cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, 'sheet_plan.png'), output_width=1600)
    doc = ezdxf.new('R2010', setup=False); doc.units = ezdxf.units.MM; msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (SW, 0), (SW, SH), (0, SH)], close=True)
    for x, y, rw, rh in rects: msp.add_lwpolyline([(x, SH - y), (x + rw, SH - y), (x + rw, SH - y - rh), (x, SH - y - rh)], close=True)
    doc.saveas(os.path.join(OUT, 'sheet_plan.dxf'))

if __name__ == '__main__':
    tb = bbox(offset(rrect(0, 0, 100, 100, 10), 2)); tc = bbox(offset(circle(0, 0, 50), 2))
    assert abs(tb[0] + 2) < .05 and abs(tb[2] - 102) < .05 and abs(tc[2] - 52) < .05, ('bleed must grow outward', tb, tc)
    only = sys.argv[1:]
    for pid, title, fn in PLATES:
        if only and pid not in only: continue
        globals()['PW'], globals()['PH'] = SIZE.get(pid, (600, 900))
        items = fn(); check(items, pid); write_plate(pid, title, items)
    if not only: write_sheet_plan()
