"""Merge the six plates: out/all_plates_print.pdf (one page per plate, true size) and out/all_plates_cut.dxf
(every plate's cut paths placed where the plate sits on the 2440×1220 sheet, as in sheet_plan; plates 1-4 turned 90°).
Run after tools/build.py:  python -I tools/merge.py
"""
import os
import ezdxf
from pypdf import PdfWriter, PdfReader
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out')
w = PdfWriter()
for i in range(1, 7): w.append(PdfReader(os.path.join(OUT, f'plate_{i}_print.pdf')))
w.add_metadata({'/Title': 'Elegance Story — forex plates 1-6 (print, 1:1 mm)'}); w.write(os.path.join(OUT, 'all_plates_print.pdf'))
K, SH = 4, 1220
place = {1: (0, 0, True), 2: (0, 600 + K, True), 3: (900 + K, 0, True), 4: (900 + K, 600 + K, True), 5: (1800 + 2 * K, 0, False), 6: (1800 + 2 * K, 900 + K, False)}
doc = ezdxf.new('R2010', setup=False); doc.units = ezdxf.units.MM; msp = doc.modelspace()
for name, col in (('CUT', 6), ('PLATES', 5), ('SHEET', 7), ('LABELS', 3)): doc.layers.add(name, color=col)
msp.add_lwpolyline([(0, 0), (2440, 0), (2440, SH), (0, SH)], close=True, dxfattribs={'layer': 'SHEET'})
n = 0
for i, (sx, sy, rot) in place.items():
    src = ezdxf.readfile(os.path.join(OUT, f'plate_{i}_cut.dxf')).modelspace()
    pw, ph = 600, (301 if i == 6 else 900); bw, bh = (ph, pw) if rot else (pw, ph); ox, oy = sx, SH - sy - bh
    T = (lambda x, y, ox=ox, oy=oy: (ox + y, oy + (pw - x))) if rot else (lambda x, y, ox=ox, oy=oy: (ox + x, oy + y))
    msp.add_lwpolyline([T(0, 0), T(pw, 0), T(pw, ph), T(0, ph)], close=True, dxfattribs={'layer': 'PLATES'})
    for e in src:
        if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == 'CUT':
            msp.add_lwpolyline([T(p[0], p[1]) for p in e.get_points()], close=True, dxfattribs={'layer': 'CUT'}); n += 1
    msp.add_text(f'PLATE {i}', height=30, dxfattribs={'layer': 'LABELS'}).set_placement((ox + 15, oy + bh - 45))
doc.saveas(os.path.join(OUT, 'all_plates_cut.dxf'))
k = .7; W, H = int(2440 * k) + 20, int(SH * k) + 20; im = Image.new('RGB', (W, H), 'white'); g = ImageDraw.Draw(im)
col = {'CUT': (236, 0, 140), 'PLATES': (28, 150, 233), 'SHEET': (0, 0, 0)}
for e in doc.modelspace():
    if e.dxftype() == 'LWPOLYLINE':
        pts = [(10 + p[0] * k, H - 10 - p[1] * k) for p in e.get_points()]; g.line(pts + [pts[0]], fill=col[e.dxf.layer], width=1 if e.dxf.layer == 'CUT' else 2)
    elif e.dxftype() == 'TEXT': g.text((10 + e.dxf.insert[0] * k, H - 10 - e.dxf.insert[1] * k - 20), e.dxf.text, fill=(0, 120, 60))
im.save(os.path.join(OUT, 'all_plates_cut_preview.png'))
print('all_plates_print.pdf:', len(PdfReader(os.path.join(OUT, 'all_plates_print.pdf')).pages), 'pages · all_plates_cut.dxf:', n, 'pieces')
