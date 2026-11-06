"""Fix a Flow-generated plaque for print: paste the real QR code (sharp) where Flow drew its code, put the official
logo back where Flow drew it, upscale to 1772 px (15 cm at 300 dpi), add a 2 mm bleed version, and check the scan.
Usage: python -I tools/fix_flow.py <flow.png> <key> <url> <logo.jpg> <circle|square>
Writes flow_results/fixed_<key>.png and fixed_<key>_bleed.png.
"""
import sys, os
import cv2, numpy as np, segno
from PIL import Image, ImageDraw
src, key, url, logo, shape = sys.argv[1:6]
OUT = 1772; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DST = os.path.join(ROOT, 'flow_results')
cv = cv2.imread(src); h, w = cv.shape[:2]
before = cv2.QRCodeDetector().detectAndDecode(cv)[0]
# 1 where Flow put its code (bottom right): the code's own corners
x0c, y0c = int(w * .6), int(h * .55); ok, pts = cv2.QRCodeDetector().detect(cv[y0c:, x0c:])
if not ok: sys.exit(f'{key}: no QR shape found in {src}')
p = pts.reshape(-1, 2) + [x0c, y0c]; qx0, qy0 = p.min(0); qx1, qy1 = p.max(0)
# 2 where Flow put the logo (bottom middle, between the hand and the code)
lx0, lx1, ly0, ly1 = int(w * .33), int(qx0 - w * .02), int(h * .62), int(h * .97)
sub = cv[ly0:ly1, lx0:lx1]; g = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
if shape == 'circle':   # white ring around the logo
    m = (g > 215).astype(np.uint8) * 255
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)
    (cx, cy), r = cv2.minEnclosingCircle(c); region = ('circle', lx0 + cx, ly0 + cy, r)
else:                   # dark rounded square behind the logo
    m = (g < 55).astype(np.uint8) * 255; m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea)
    bx, by, bw, bh = cv2.boundingRect(c); region = ('square', lx0 + bx, ly0 + by, bw, bh)
im = Image.open(src).convert('RGB'); k = OUT / im.width; im = im.resize((OUT, OUT), Image.LANCZOS); d = ImageDraw.Draw(im)
# real QR, centred on Flow's code, white quiet zone
cx, cy, side = (qx0 + qx1) / 2 * k, (qy0 + qy1) / 2 * k, max(qx1 - qx0, qy1 - qy0) * k * 1.02
d.rectangle([cx - side / 2 - 10, cy - side / 2 - 10, cx + side / 2 + 10, cy + side / 2 + 10], fill='white')
q = segno.make(url, error='h'); n = len(q.matrix); px = max(1, int(side // n)); side = px * n
qi = Image.fromarray(np.where(np.array(q.matrix, dtype=np.uint8), 0, 255).astype(np.uint8)).resize((side, side), Image.NEAREST).convert('RGB')
im.paste(qi, (int(cx - side / 2), int(cy - side / 2)))
# official logo, unchanged
lg = Image.open(logo).convert('RGB')
if region[0] == 'circle':
    _, ccx, ccy, r = region; ri = int(r * k * .9); s = 2 * ri; lg = lg.resize((s, s), Image.LANCZOS)
    mk = Image.new('L', (s, s), 0); ImageDraw.Draw(mk).ellipse([0, 0, s - 1, s - 1], fill=255); im.paste(lg, (int(ccx * k - ri), int(ccy * k - ri)), mk)
else:
    _, bx, by, bw, bh = region; s = int(min(bw, bh) * k * .96); lg = lg.resize((s, s), Image.LANCZOS)
    mk = Image.new('L', (s, s), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, s - 1, s - 1], int(s * .1), fill=255)
    im.paste(lg, (int((bx + bw / 2) * k - s / 2), int((by + bh / 2) * k - s / 2)), mk)
os.makedirs(DST, exist_ok=True); out = os.path.join(DST, f'fixed_{key}.png'); im.save(out)
a = cv2.imread(out); after = cv2.QRCodeDetector().detectAndDecode(a)[0]
pb = round(2 / 150 * OUT); cv2.imwrite(os.path.join(DST, f'fixed_{key}_bleed.png'), cv2.copyMakeBorder(a, pb, pb, pb, pb, cv2.BORDER_REPLICATE))
print(f'{key}: Flow code scans: {"yes" if before == url else "NO"} · fixed code scans: {"yes" if after == url else "NO"} · logo region {region[0]}')
if after != url: sys.exit(1)
