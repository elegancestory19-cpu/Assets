// engine.js: the Dark Tech Keynote engine adapted for Elegance Story (9:16, Arabic RTL, cyan accent).
// Adapted from the style's engine: stage, grid, panels, caret, flight, light reveal, scramble, toast, camera.
import { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU } from '/core/lib.js';
export { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU };

export const W = 1080, H = 1920;
// safe column: x 0..940, y 180..1540 → centre of the content column
export const CX = 500, TOP = 180, BOT = 1540, RIGHT = 940;
export const PAL = {
  bg0: '#070708', bg1: '#121622', surf: '#11141B', surf2: '#191D27', surf3: '#222734',
  line: 'rgba(255,255,255,.08)', text: '#E8EAF0', dim: '#8A90A0', mute: '#5C6272',
  accent: '#1CCEE9', red: '#FF4D5E', cool: '#2457D6',
  blue: '#6F8FE0', purple: '#9C7BC8', magenta: '#C77BB0',
};
export const FONT = { ar: 'Cairo', disp: 'InterTight', mono: 'JBMono' };
export const font = (px, wt = 600, fam = 'ar') => `${wt} ${px}px ${FONT[fam] || fam}`;
export function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
}
export function mix(h1, h2, t) {
  const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16);
  const c = s => Math.round(lerp(a >> s & 255, b >> s & 255, t));
  return `rgb(${c(16)},${c(8)},${c(0)})`;
}
const _pool = {};
export function buf(name, w = W, h = H) {
  let c = _pool[name];
  if (!c || c.width !== w || c.height !== h) { c = _pool[name] = document.createElement('canvas'); c.width = w; c.height = h; }
  const g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
  g.clearRect(0, 0, w, h);
  return [c, g];
}
export function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2))); }

// ── stage
export function bg(g, o = {}) {
  const { lift = 1, cool = 1 } = o;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = PAL.bg0; g.fillRect(0, 0, W, H);
  const gr = g.createRadialGradient(W * 0.48, H * 0.3, 0, W * 0.48, H * 0.3, H * 0.62);
  gr.addColorStop(0, rgba(PAL.bg1, 0.95 * lift)); gr.addColorStop(1, rgba(PAL.bg0, 0));
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  if (cool > 0) glow(g, W * 0.82, H * 0.16, 820, PAL.cool, 0.07 * cool);
  g.restore();
}
export function glow(g, x, y, r, color, a) {
  if (a <= 0 || r <= 0) return;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, a)); gr.addColorStop(0.45, rgba(color, a * 0.35)); gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
}
export function grid(g, o = {}) {
  const { ox = 0, oy = 0, scale = 1, module = 48, alpha = 1, major = 4 } = o;
  const step = module * scale; if (step < 4 || alpha <= 0) return;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.lineWidth = 1;
  const i0 = Math.floor(-ox / step), i1 = Math.ceil((W - ox) / step), j0 = Math.floor(-oy / step), j1 = Math.ceil((H - oy) / step);
  for (let pass = 0; pass < 2; pass++) {
    g.strokeStyle = `rgba(255,255,255,${(pass ? 0.06 : 0.032) * alpha})`; g.beginPath();
    for (let i = i0; i <= i1; i++) { if ((i % major === 0) !== !!pass) continue; const x = Math.round(ox + i * step) + 0.5; g.moveTo(x, 0); g.lineTo(x, H); }
    for (let j = j0; j <= j1; j++) { if ((j % major === 0) !== !!pass) continue; const y = Math.round(oy + j * step) + 0.5; g.moveTo(0, y); g.lineTo(W, y); }
    g.stroke();
  }
  g.restore();
}
export function vignette(g, a = 0.55) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  const gr = g.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.72);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(0,0,0,${a})`);
  g.fillStyle = gr; g.fillRect(0, 0, W, H); g.restore();
}

// ── surfaces
export function panel(g, x, y, w, h, o = {}) {
  const { r = 22, fill = PAL.surf, stroke = PAL.line, shadow = 1, cheap = false, alpha = 1 } = o;
  g.save(); g.globalAlpha *= alpha;
  if (shadow > 0) {
    if (cheap) { g.fillStyle = `rgba(0,0,0,${0.35 * shadow})`; rr(g, x + 2, y + h * 0.05 + 4, w, h, r); g.fill(); }
    else { g.shadowColor = `rgba(0,0,0,${0.55 * shadow})`; g.shadowBlur = Math.min(90, 18 + h * 0.15); g.shadowOffsetY = Math.min(40, 6 + h * 0.05); g.fillStyle = fill; rr(g, x, y, w, h, r); g.fill(); g.shadowColor = 'transparent'; }
  }
  const gr = g.createLinearGradient(0, y, 0, y + h);
  gr.addColorStop(0, mix(fill, '#2A3040', 0.25)); gr.addColorStop(Math.min(1, 70 / Math.max(h, 1)), fill); gr.addColorStop(1, fill);
  g.fillStyle = gr; rr(g, x, y, w, h, r); g.fill();
  g.lineWidth = 1; g.strokeStyle = stroke; rr(g, x + 0.5, y + 0.5, w - 1, h - 1, r); g.stroke();
  g.strokeStyle = 'rgba(255,255,255,.07)'; g.beginPath(); g.moveTo(x + r, y + 1.5); g.lineTo(x + w - r, y + 1.5); g.stroke();
  g.restore();
}
/** Window with an RTL title bar: title on the right, mono code on the left. Returns the content rect. */
export function windowBox(g, x, y, w, h, o = {}) {
  const { title = '', code = '', alpha = 1, r = 26, bar = 64, rim = 0 } = o;
  g.save(); g.globalAlpha *= alpha;
  panel(g, x, y, w, h, { r });
  g.fillStyle = 'rgba(255,255,255,.025)'; rr(g, x + 1, y + 1, w - 2, bar, r); g.fill();
  g.fillStyle = PAL.line; g.fillRect(x, y + bar, w, 1);
  // small glyph: accent square dot (product's own mark, not an app icon)
  g.fillStyle = PAL.accent; g.shadowColor = rgba(PAL.accent, 0.8); g.shadowBlur = 10;
  rr(g, x + w - 34, y + bar / 2 - 6, 12, 12, 3); g.fill(); g.shadowColor = 'transparent';
  text(g, title, x + w - 52, y + bar / 2 + 2, { px: 28, wt: 700, color: PAL.text, align: 'right' });
  if (code) mono(g, code, x + 26, y + bar / 2 + 1, { px: 20, color: PAL.mute, align: 'left' });
  if (rim > 0) { g.strokeStyle = rgba(PAL.accent, 0.8 * rim); g.lineWidth = 2; g.shadowColor = rgba(PAL.accent, rim); g.shadowBlur = 24; rr(g, x + 1, y + 1, w - 2, h - 2, r); g.stroke(); g.shadowColor = 'transparent'; }
  g.restore();
  return [x, y + bar + 1, w, h - bar - 1];
}

// ── type (Arabic RTL by default)
export function text(g, s, x, y, o = {}) {
  const { px = 40, wt = 600, color = PAL.text, align = 'center', alpha = 1, fam = 'ar', base = 'middle', glowC = null } = o;
  if (alpha <= 0) return 0;
  g.save(); g.globalAlpha *= alpha; g.font = font(px, wt, fam); g.direction = fam === 'ar' ? 'rtl' : 'ltr';
  g.textAlign = align; g.textBaseline = base; g.fillStyle = color;
  if (glowC) { g.shadowColor = glowC; g.shadowBlur = px * 0.5; }
  g.fillText(s, x, y); const w = g.measureText(s).width; g.restore(); return w;
}
export function mono(g, s, x, y, o = {}) { return text(g, s, x, y, { wt: 500, ...o, fam: 'mono' }); }
export function measure(g, s, px, wt = 600, fam = 'ar') { g.save(); g.font = font(px, wt, fam); g.direction = fam === 'ar' ? 'rtl' : 'ltr'; const w = g.measureText(s).width; g.restore(); return w; }

/** Chip: pill with text. RTL Arabic or mono code. */
export function chip(g, s, cx, cy, o = {}) {
  const { px = 28, fam = 'ar', a = 1, on = 0, wt = 600 } = o;
  if (a <= 0) return;
  const w = measure(g, s, px, wt, fam) + px * 1.4, h = px * 1.7;
  g.save(); g.globalAlpha *= a;
  g.fillStyle = on > 0 ? rgba(PAL.accent, 0.14 * on + 0.04) : 'rgba(255,255,255,.05)'; rr(g, cx - w / 2, cy - h / 2, w, h, h / 2); g.fill();
  g.strokeStyle = on > 0 ? rgba(PAL.accent, 0.6 * on) : 'rgba(255,255,255,.12)'; g.lineWidth = 1; rr(g, cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, h / 2); g.stroke();
  g.restore();
  text(g, s, cx, cy + (fam === 'ar' ? px * 0.06 : 0), { px, wt, fam, alpha: a, color: on > 0.5 ? PAL.text : PAL.dim });
  return w;
}
/** Accent check mark in a circle */
export function check(g, cx, cy, r, p = 1, a = 1) {
  if (p <= 0 || a <= 0) return;
  g.save(); g.globalAlpha *= a;
  g.fillStyle = PAL.accent; g.shadowColor = rgba(PAL.accent, 0.8); g.shadowBlur = r;
  g.beginPath(); g.arc(cx, cy, r * back(clamp(p * 1.6), 1.6), 0, TAU); g.fill(); g.shadowColor = 'transparent';
  const q = clamp((p - 0.3) / 0.7);
  if (q > 0) {
    g.strokeStyle = '#04161A'; g.lineWidth = r * 0.24; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath();
    const P = [[cx - r * 0.42, cy + r * 0.02], [cx - r * 0.1, cy + r * 0.34], [cx + r * 0.46, cy - r * 0.3]];
    g.moveTo(...P[0]);
    if (q < 0.4) g.lineTo(lerp(P[0][0], P[1][0], q / 0.4), lerp(P[0][1], P[1][1], q / 0.4));
    else { g.lineTo(...P[1]); const u = (q - 0.4) / 0.6; g.lineTo(lerp(P[1][0], P[2][0], u), lerp(P[1][1], P[2][1], u)); }
    g.stroke();
  }
  g.restore();
}
export function redBadge(g, x, y, s, k = 1) {
  g.save(); g.font = font(22 * k, 700); g.direction = 'rtl';
  const w = Math.max(34 * k, g.measureText(s).width + 22 * k), h = 34 * k;
  g.fillStyle = PAL.red; g.shadowColor = rgba(PAL.red, 0.5); g.shadowBlur = 10 * k; rr(g, x - w / 2, y - h / 2, w, h, h / 2); g.fill(); g.shadowColor = 'transparent';
  g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, x, y + 2 * k); g.restore();
}

// ── the living element
export function caret(g, x, y, h, o = {}) {
  const { sx = 1, sy = 1, on = 1, glow: gl = 1, color = PAL.accent, alpha = 1, wr = 1 / 12 } = o;
  if (on <= 0.001 || alpha <= 0) return;
  const w = Math.max(3, h * wr) * sx, hh = h * sy;
  g.save(); g.globalAlpha *= alpha * on;
  if (gl > 0) { glow(g, x, y, hh * 0.9 * gl, color, 0.22 * gl); g.shadowColor = rgba(color, 0.9); g.shadowBlur = hh * 0.22 * gl; }
  g.fillStyle = color; rr(g, x - w / 2, y - hh / 2, w, hh, Math.min(w / 2, 6)); g.fill();
  g.restore();
}
/** Pointer arrow (the cursor), tip at (x,y) */
export function pointer(g, x, y, s = 1, o = {}) {
  const { sx = 1, sy = 1, alpha = 1 } = o; if (alpha <= 0) return;
  g.save(); g.globalAlpha *= alpha; g.translate(x, y); g.scale(s * sx, s * sy);
  const p = new Path2D('M0 0 L0 46 L12 35 L20 54 L29 50 L21 32 L37 32 Z');
  g.shadowColor = rgba(PAL.accent, 0.9); g.shadowBlur = 22; g.fillStyle = PAL.accent; g.fill(p); g.shadowColor = 'transparent';
  g.lineWidth = 2; g.strokeStyle = 'rgba(255,255,255,.75)'; g.stroke(p); g.restore();
}
export function trail(g, pts, o = {}) {
  const { color = PAL.accent, width = 6, alpha = 1 } = o;
  if (pts.length < 2) return;
  g.save(); g.lineCap = 'round';
  for (let i = 1; i < pts.length; i++) {
    const u = i / (pts.length - 1);
    g.strokeStyle = rgba(color, alpha * u * u * 0.9); g.lineWidth = width * (0.25 + 0.75 * u);
    g.shadowColor = rgba(color, 0.6 * u * alpha); g.shadowBlur = 18 * u;
    g.beginPath(); g.moveTo(...pts[i - 1]); g.lineTo(...pts[i]); g.stroke();
  }
  g.restore();
}

// ── images
/** Draw an image (cover-fit) into a rounded rect with a 1 px light border */
export function pic(g, img, x, y, w, h, o = {}) {
  const { r = 18, alpha = 1, border = true, zoom = 1, fx = 0.5, fy = 0.5, bright = 1 } = o;
  if (alpha <= 0 || w < 1 || h < 1) return;
  g.save(); g.globalAlpha *= alpha; rr(g, x, y, w, h, r); g.clip();
  const s = Math.max(w / img.width, h / img.height) * zoom, iw = img.width * s, ih = img.height * s;
  if (bright !== 1) g.filter = `brightness(${bright})`;
  g.drawImage(img, x + (w - iw) * fx, y + (h - ih) * fy, iw, ih); g.filter = 'none';
  g.restore();
  if (border) { g.save(); g.globalAlpha *= alpha; g.strokeStyle = 'rgba(255,255,255,.14)'; g.lineWidth = 1; rr(g, x + 0.5, y + 0.5, w - 1, h - 1, r); g.stroke(); g.restore(); }
}
/** The official colour logo: drawn unchanged ('lighten' over the dark stage hides its black square), edges faded. */
export function logo(g, img, cx, cy, size, a = 1) {
  if (a <= 0) return;
  const [c, t] = buf('logoMask', 1024, 1024);
  t.drawImage(img, 0, 0, 1024, 1024);
  t.globalCompositeOperation = 'destination-in';
  const m = t.createRadialGradient(512, 512, 330, 512, 512, 512);
  m.addColorStop(0, 'rgba(0,0,0,1)'); m.addColorStop(1, 'rgba(0,0,0,0)');
  t.fillStyle = m; t.fillRect(0, 0, 1024, 1024);
  g.save(); g.globalAlpha *= a; g.globalCompositeOperation = 'lighten'; g.drawImage(c, cx - size / 2, cy - size / 2, size, size); g.restore();
}

// ── motion
export function flyPose(from, to, p, o = {}) {
  const { over = 1.3 } = o; const q = back(clamp(p), over), r = spring(clamp(p) * 1.2, 9, 0.42);
  return { x: lerp(from.x, to.x, q), y: lerp(from.y, to.y, q), rot: lerp(from.rot || 0, to.rot || 0, clamp(r)), s: lerp(from.s ?? 1, to.s ?? 1, eo(clamp(p))) };
}
/** Curved flight: quadratic bezier with a side bend, back-eased along the path */
export function curve(from, to, p, bend = 0.25, over = 1.25) {
  const q = back(clamp(p), over), mx = (from.x + to.x) / 2, my = (from.y + to.y) / 2;
  const dx = to.x - from.x, dy = to.y - from.y, cx = mx - dy * bend, cy = my + dx * bend;
  const u = q, a = (1 - u) * (1 - u), b = 2 * (1 - u) * u, c = u * u;
  return { x: a * from.x + b * cx + c * to.x, y: a * from.y + b * cy + c * to.y };
}
/** UI expand: rect grows from a source rect, landing with a small overshoot. p 0..1 */
export function expand(src, dst, p) {
  const q = back(clamp(p), 1.25);
  return { x: lerp(src.x, dst.x, q), y: lerp(src.y, dst.y, q), w: Math.max(1, lerp(src.w, dst.w, q)), h: Math.max(1, lerp(src.h, dst.h, q)) };
}
/** CRT-off collapse: vertical squash into a line, then into a point. p 0..1 → {sx, sy} */
export function crtOff(p) {
  const a = ei(clamp(p / 0.6)), b = ei(clamp((p - 0.6) / 0.4));
  return { sy: lerp(1, 0.012, a), sx: lerp(1, 0.0, b) };
}

/** Light-sweep reveal of any image/canvas into (dx,dy,dw,dh) */
export function lightReveal(g, src, dx, dy, dw, dh, p, o = {}) {
  const { base = 0.07, angle = 0.62, soft = 320, band = 110, glint = 0.2, r = 18, tint = '235,240,255' } = o;
  const [c, t] = buf('reveal', Math.ceil(dw), Math.ceil(dh));
  t.save(); rr(t, 0, 0, dw, dh, r); t.clip();
  const s = Math.max(dw / src.width, dh / src.height); t.drawImage(src, (dw - src.width * s) / 2, (dh - src.height * s) / 2, src.width * s, src.height * s); t.restore();
  const ca = Math.cos(angle), sa = Math.sin(angle), L = Math.abs(dw * ca) + Math.abs(dh * sa);
  const front = -soft + p * (L + soft * 2), p0 = [dw / 2 - ca * L / 2, dh / 2 - sa * L / 2], at = d => [p0[0] + ca * d, p0[1] + sa * d];
  const [c1, t1] = buf('reveal1', Math.ceil(dw), Math.ceil(dh));
  t1.drawImage(c, 0, 0); t1.globalCompositeOperation = 'destination-in';
  const A = at(front - soft), B = at(front); const gr = t1.createLinearGradient(A[0], A[1], B[0], B[1]);
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); t1.fillStyle = gr; t1.fillRect(0, 0, dw, dh);
  g.save(); g.globalAlpha *= base; g.drawImage(c, dx, dy); g.restore();
  g.drawImage(c1, dx, dy);
  if (glint > 0 && p > 0 && p < 1) {
    const [c2, t2] = buf('reveal2', Math.ceil(dw), Math.ceil(dh));
    t2.drawImage(c, 0, 0); t2.globalCompositeOperation = 'source-in';
    const A2 = at(front - band * 1.6), B2 = at(front + band * 0.4); const g2 = t2.createLinearGradient(A2[0], A2[1], B2[0], B2[1]);
    g2.addColorStop(0, `rgba(${tint},0)`); g2.addColorStop(0.7, `rgba(${tint},${glint})`); g2.addColorStop(1, `rgba(${tint},0)`);
    t2.fillStyle = g2; t2.fillRect(0, 0, dw, dh);
    g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(c2, dx, dy); g.restore();
  }
}

const GLYPH = '0123456789#%/*+=<>?$&@';
/** Glyph noise → number; per-character lock times; LTR text centred at x */
export function scramble(g, s, x, y, t, locks, o = {}) {
  const { px = 300, wt = 600, color = PAL.text, colorOf = null, tracking = -0.045, fps = 24, glowC = null } = o;
  g.save(); g.font = font(px, wt, 'disp'); g.textBaseline = 'alphabetic'; g.direction = 'ltr'; g.textAlign = 'left';
  const ch = [...s], tw = ch.map(c => g.measureText(c).width), adv = tw.map(w => w + tracking * px);
  const total = adv.reduce((a, b) => a + b, 0) - tracking * px; let cx = x - total / 2; const f = Math.floor(t * fps);
  if (glowC) { g.shadowColor = glowC; g.shadowBlur = px * 0.25; }
  ch.forEach((c, i) => {
    const lk = locks[i] ?? locks[locks.length - 1], col = colorOf ? colorOf(i) : color, dig = /[0-9]/.test(c);
    g.fillStyle = col;
    if (t < lk && dig) {
      const gc = GLYPH[Math.floor(hash(f * 13.7 + i * 91.3) * GLYPH.length)];
      for (let k = 0; k < 3; k++) { g.globalAlpha = [0.85, 0.3, 0.14][k]; g.fillText(gc, cx + (tw[i] - g.measureText(gc).width) / 2, y - k * px * 0.09); }
      g.globalAlpha = 1;
    } else if (t >= lk) {
      const d = t - lk, dy = d < 0.3 ? -px * 0.12 * Math.exp(-d * 14) * Math.cos(d * 40) : 0;
      g.globalAlpha = clamp(d * 30 + 0.4); g.fillText(c, cx, y + dy); g.globalAlpha = 1;
    }
    cx += adv[i];
  });
  g.restore(); return total;
}

/** Caption toast (RTL): dark pill, cyan speaking dot on the right; wraps to two balanced lines when long */
export function toast(g, s, a, o = {}) {
  if (a <= 0) return;
  const { y = 1530, px = 38, dense = 0, maxW = 880 } = o;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.font = font(px, 600); g.direction = 'rtl';
  let lines = [s];
  if (g.measureText(s).width + px * 2.6 > maxW) {
    const w = s.split(' '); let best = null;
    for (let i = 1; i < w.length; i++) { const A = w.slice(0, i).join(' '), B = w.slice(i).join(' '); const m = Math.max(g.measureText(A).width, g.measureText(B).width); if (!best || m < best[0]) best = [m, [A, B]]; }
    lines = best[1];
  }
  const tw = Math.max(...lines.map(l => g.measureText(l).width)), lh = px * 1.35, h = px * 0.75 + lh * lines.length, w = tw + px * 2.6, x = CX - w / 2, yy = y - h + (1 - eo(a)) * 12;
  g.globalAlpha = eo(a);
  g.shadowColor = 'rgba(0,0,0,.5)'; g.shadowBlur = 40; g.shadowOffsetY = 10;
  const rad = Math.min(h / 2, px * 1.0);
  g.fillStyle = `rgba(12,14,19,${0.76 + 0.14 * dense})`; rr(g, x, yy, w, h, rad); g.fill(); g.shadowColor = 'transparent';
  g.strokeStyle = 'rgba(255,255,255,.10)'; g.lineWidth = 1; rr(g, x + 0.5, yy + 0.5, w - 1, h - 1, rad); g.stroke();
  g.fillStyle = PAL.accent; g.shadowColor = rgba(PAL.accent, 0.8); g.shadowBlur = 10; g.beginPath(); g.arc(x + w - px * 0.95, yy + px * 0.375 + lh / 2, px * 0.15, 0, TAU); g.fill(); g.shadowColor = 'transparent';
  g.fillStyle = PAL.text; g.textAlign = 'right'; g.textBaseline = 'middle';
  lines.forEach((l, i) => g.fillText(l, x + w - px * 1.5, yy + px * 0.375 + lh * (i + 0.5) + px * 0.08));
  g.restore();
  return [x, yy, w, h];
}

/** 2.5D camera looking at world (x,y) */
export function camera(c) {
  const { x = W / 2, y = H / 2, zoom = 1, rot = 0, sx = 0, sy = 0 } = c;
  const apply = (g, z = 0) => {
    const d = 1 / zoom - z, s = 1 / Math.max(d, 0.02);
    g.setTransform(1, 0, 0, 1, 0, 0); g.translate(W / 2 + sx, H / 2 + sy); g.rotate(rot); g.scale(s, s); g.translate(-x, -y); return s;
  };
  return { x, y, zoom, rot, apply };
}
