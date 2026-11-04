// main.js: renderer, light, cameras per shot, HUD (captions, 3.20 m measure, end card), event export
import * as THREE from 'three';
import { clamp, seg, ss, eio, eo, lerp } from '/core/lib.js';
import { DUR, T, SKY, LINES } from './story.js';
import { makePost } from './post.js';
import { makeSea } from './sea.js';
import { buildWorld, ISL } from './world.js';

const W = 1080, H = 1920, QS = new URLSearchParams(location.search), SSAA = +(QS.get('ssaa') ?? 1);
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('stage').appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-3, 3, 5, -5, 1, 1600);
const post = makePost(renderer, scene, camera, W, H, { ssaa: SSAA, aoRadius: .45, aoScale: 1.4, aoThickness: .8 });
post.bloom.threshold = .9; post.bloom.radius = .5;

const ld = new THREE.TextureLoader();
const loadTex = u => new Promise(res => ld.load(u, t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; res(t); }));
const tex = { logo3d: await loadTex('img/logo3d.jpg'), tag: await loadTex('img/logo_tag.jpg') };
const logoImg = await new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = 'img/logo3d.jpg'; });

const sea = makeSea(scene);
const world = buildWorld(scene, tex);

const hemi = new THREE.HemisphereLight('#eef6fb', '#c6b89c', 1.1); scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff6e8', 2.6); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -.0006; sun.shadow.normalBias = .02; sun.shadow.radius = 3;
Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 140 }); sun.shadow.camera.updateProjectionMatrix();
scene.add(sun, sun.target);

const C = h => new THREE.Color(h);
const SK = SKY.map(k => ({ t: k[0], zen: C(k[1]), hor: C(k[2]), deep: C(k[3]), shal: C(k[4]), sun: C(k[5]), sunI: k[6], hs: C(k[7]), hg: C(k[8]), hI: k[9], el: k[10], az: k[11], night: k[12] }));
function skyAt(t) {
  let i = 0; while (i < SK.length - 2 && t > SK[i + 1].t) i++;
  const a = SK[i], b = SK[i + 1], u = ss(seg(t, a.t, b.t)), o = {};
  for (const k of ['zen', 'hor', 'deep', 'shal', 'sun', 'hs', 'hg']) o[k] = a[k].clone().lerp(b[k], u);
  for (const k of ['sunI', 'hI', 'el', 'az', 'night']) o[k] = lerp(a[k], b[k], u);
  return o;
}

// ── cameras: orthographic; target / azimuth / elevation / frustum height
const DEG = Math.PI / 180, V2 = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u)];
const TOWN = [0, -.4];
let CAM = {};
function cam(t) {
  let tg2, ty = .5, az, el, fh, tilt = .3;
  if (t < 3.0) {                              // 1 top-down map tilting into isometric
    const u = eio(seg(t, T.tilt0, T.tilt1)); tg2 = ISL.start; ty = .25; el = lerp(88, 32, u); az = lerp(60, 42, u); fh = lerp(4.2, 6.0, u);
  } else if (t < 7.5) {                       // 2 trailing the idea onto the design island
    const u = ss(seg(t, 3.6, 5.2)); tg2 = V2(ISL.start, ISL.i1, u); el = 32; az = lerp(42, 54, seg(t, 3, 7.5)); fh = lerp(6.0, 7.0, u);
  } else if (t < 13.5) {                      // 3 lateral truck along the bridge, then close on the UV bed
    const u = ss(seg(t, 7.6, 9.3)); tg2 = V2(ISL.i1, ISL.i2, u); el = lerp(32, 36, u); az = lerp(54, 62, u); fh = lerp(7.2, 5.2, ss(seg(t, 9.0, 10.6)));
  } else if (t < 18.5) {                      // 4 to the gifts island, then a turntable
    const u = ss(seg(t, 13.5, 14.7)); tg2 = V2(ISL.i2, ISL.i3, u); el = 32; az = 62 + 70 * eio(seg(t, 14.4, 18.5)); fh = lerp(6.6, 5.4, ss(seg(t, 14.0, 15.0)));
  } else if (t < 24.5) {                      // 5 the facade island: elevation drops (more sky), the sun sets
    const u = ss(seg(t, 18.5, 19.7)); tg2 = V2(ISL.i3, ISL.i4, u); ty = lerp(.5, 1.0, u); el = lerp(34, 22, ss(seg(t, 20.5, 24.5))); az = lerp(132, 150, seg(t, 18.5, 24.5)); fh = lerp(6.6, 8.2, ss(seg(t, 19.0, 20.6)));
  } else {                                    // 6–7 night: pull out and rise back to the map; end card lowers the town
    const u = eio(seg(t, 24.6, 28.8)), e = eio(seg(t, T.end - .2, T.end + 1.2));
    tg2 = V2(ISL.i4, TOWN, u); tg2 = [tg2[0], tg2[1] + 4.2 * e]; ty = lerp(1.0, .3, u); el = lerp(22, 78, u); az = lerp(150, 180, u); fh = lerp(8.2, 19, u) * lerp(1, 1.22, e); tilt = lerp(.3, .38, u);
  }
  const tg = [tg2[0], ty, tg2[1]];
  const D = Math.max(300, fh * 3), ce = Math.cos(el * DEG);
  camera.position.set(tg[0] + D * ce * Math.sin(az * DEG), tg[1] + D * Math.sin(el * DEG), tg[2] + D * ce * Math.cos(az * DEG));
  camera.up.set(0, 1, 0); camera.lookAt(tg[0], tg[1], tg[2]);
  const fw = fh * W / H; camera.left = -fw / 2; camera.right = fw / 2; camera.top = fh / 2; camera.bottom = -fh / 2; camera.near = 1; camera.far = D + fh * 6 + 800; camera.updateProjectionMatrix();
  const cot = 1 / Math.tan(el * DEG);
  post.comp.camDist.value = D; post.comp.hz0.value = Math.max(.1 * fh * cot, 1.5); post.comp.hz1.value = Math.max(.52 * fh * cot, 4);
  post.tilt.fy.value = .5; post.tilt.band.value = tilt;
  CAM = { tg, az, el, fh };
}

// ── HUD
const ov = document.getElementById('ov'), g = ov.getContext('2d');
const iconTop = t => t < 3 ? '#f5c2b0' : t < 21 ? '#a8d8a0' : t < 24.5 ? '#ffa860' : '#ffc676';
function hexIcon(x, y, s, topc) {
  const pts = [0, 1, 2, 3, 4, 5].map(i => [x + Math.cos(i * Math.PI / 3) * s, y + Math.sin(i * Math.PI / 3) * s * .58]), dy = s * .55;
  g.save(); g.fillStyle = '#b88a5e'; g.beginPath(); g.moveTo(...pts[0]); [0, 1, 2, 3].forEach(i => g.lineTo(pts[i][0], pts[i][1] + dy)); g.lineTo(...pts[3]); g.closePath(); g.fill();
  g.fillStyle = topc; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(...p) : g.moveTo(...p)); g.closePath(); g.fill(); g.restore();
}
const CX = 500;
function arText(s, x, y, px, wt, col, o = {}) {
  g.save(); g.font = `${wt} ${px}px Cairo`; g.direction = o.ltr ? 'ltr' : 'rtl'; g.textAlign = o.align || 'center'; g.textBaseline = 'middle';
  if (o.fam) g.font = `${wt} ${px}px ${o.fam}`;
  g.shadowColor = o.shadow ?? 'rgba(15,25,55,.6)'; g.shadowBlur = o.blur ?? 14; g.shadowOffsetY = 2; g.fillStyle = col; g.globalAlpha = o.alpha ?? 1;
  g.fillText(s, x, y); const w = g.measureText(s).width; g.restore(); return w;
}
function wrap2(s, px, maxW) {
  g.save(); g.font = `700 ${px}px Cairo`; g.direction = 'rtl';
  if (g.measureText(s).width <= maxW) { g.restore(); return [s]; }
  const w = s.split(' '); let best = null;
  for (let i = 1; i < w.length; i++) { const A = w.slice(0, i).join(' '), B = w.slice(i).join(' '), m = Math.max(g.measureText(A).width, g.measureText(B).width); if (!best || m < best[0]) best = [m, [A, B]]; }
  g.restore(); return best[1];
}
function project(x, y, z) { const v = new THREE.Vector3(x, y, z).project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }
function hud(t) {
  g.clearRect(0, 0, W, H);
  if (QS.get('nohud')) return;
  // captions
  const L = LINES.find(l => t >= l.cap[0] && t < l.cap[1]);
  if (L && t < T.end + 5) {
    const al = ss(seg(t, L.cap[0], L.cap[0] + .18)) * (1 - ss(seg(t, L.cap[1] - .2, L.cap[1])));
    const lines = wrap2(L.srt || L.say, 44, 780), y0 = 1450 - (lines.length - 1) * 30;
    lines.forEach((ln, i) => {
      const w = arText(ln, CX, y0 + i * 62, 44, 700, '#fffdf8', { alpha: al });
      if (i === 0) { g.save(); g.globalAlpha = al; hexIcon(CX + w / 2 + 30, y0 - 4, 15, iconTop(t)); g.restore(); }
    });
  }
  // the 3.20 m measure beside the facade
  if (t >= T.banner0 && t < T.night) {
    const a = ss(seg(t, T.banner1 - .2, T.banner1 + .2)) * (1 - ss(seg(t, T.night - .4, T.night)));
    const [x4, z4] = ISL.i4, k = eo(seg(t, T.banner0, T.banner1));
    const pc0 = project(x4 + .1, .82, z4 - .2), pc1 = project(x4 + .1, .82 + 1.3 * k, z4 - .2), off = -(.62 * H / CAM.fh);
    const p0 = [pc0[0] + off - 26, pc0[1]], p1 = [pc1[0] + off - 26, pc1[1]];
    g.save(); g.globalAlpha = Math.max(a, k * .8); g.strokeStyle = '#fffdf8'; g.lineWidth = 3; g.shadowColor = 'rgba(15,25,55,.6)'; g.shadowBlur = 8;
    g.beginPath(); g.moveTo(p0[0] + 26, p0[1]); g.lineTo(p1[0] + 26, p1[1]); g.moveTo(p0[0] + 14, p0[1]); g.lineTo(p0[0] + 38, p0[1]); g.moveTo(p1[0] + 14, p1[1]); g.lineTo(p1[0] + 38, p1[1]); g.stroke(); g.restore();
    if (a > 0) { arText('3.20', p1[0] - 2, (p0[1] + p1[1]) / 2 - 22, 54, 800, '#fffdf8', { ltr: true, align: 'right', fam: 'Cairo', alpha: a }); arText('متر', p1[0] - 2, (p0[1] + p1[1]) / 2 + 30, 34, 700, '#fffdf8', { align: 'left', alpha: a }); }
  }
  // end card (the town stays visible in the gap below)
  if (t >= T.end) {
    const a = ss(seg(t, T.end, T.end + .8));
    const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, `rgba(8,10,30,${.82 * a})`); gr.addColorStop(.55, `rgba(8,10,30,${.55 * a})`); gr.addColorStop(.75, 'rgba(8,10,30,0)');
    g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const rise = (d) => { const s = t - (T.end + d); return s < 0 ? null : (s < .28 ? 60 * Math.pow(1 - s / .28, 2) : -Math.sin((s - .28) * 14) * Math.exp(-(s - .28) * 8) * 6); };
    const lr = rise(.2); if (lr !== null) {
      g.save(); g.globalAlpha = a; g.globalCompositeOperation = 'lighten';
      const sz = 470, cy = 420 + lr; const m = g.createRadialGradient(CX, cy, sz * .3, CX, cy, sz * .5);
      // draw the official logo unchanged; the radial mask only fades its square edges
      const off = document.createElement('canvas'); off.width = off.height = sz; const og = off.getContext('2d'); og.drawImage(logoImg, 0, 0, sz, sz);
      og.globalCompositeOperation = 'destination-in'; const rg = og.createRadialGradient(sz / 2, sz / 2, sz * .3, sz / 2, sz / 2, sz * .5); rg.addColorStop(0, '#000'); rg.addColorStop(1, 'rgba(0,0,0,0)'); og.fillStyle = rg; og.fillRect(0, 0, sz, sz);
      g.drawImage(off, CX - sz / 2, cy - sz / 2); g.restore();
    }
    const rows = [['إشهار و حلول طباعة ذكية', 690, 40, 700, '#ffd89a', false], ['0772 65 83 01', 770, 50, 800, '#fffdf8', true], ['0668 89 79 07', 836, 44, 700, '#fffdf8', true], ['0553 04 54 07', 896, 44, 700, '#fffdf8', true], ['elegancestory19@gmail.com', 960, 32, 600, 'rgba(255,255,255,.85)', true], ['سطيف', 1028, 44, 800, '#fffdf8', false]];
    rows.forEach(([s, y, px, wt, col, ltr], i) => {
      const off = rise(.45 + i * .12); if (off === null) return;
      const w = arText(s, i === 1 ? CX - 60 : CX, y + off, px, wt, col, { ltr, fam: ltr ? 'JBMono' : null });
      if (i === 1) { g.save(); g.font = '700 26px Cairo'; g.direction = 'rtl'; const cw = g.measureText('واتساب').width + 28; const x = CX - 60 + w / 2 + 18;
        g.fillStyle = 'rgba(28,206,233,.22)'; g.strokeStyle = 'rgba(28,206,233,.8)'; g.beginPath(); g.roundRect(x, y + off - 21, cw, 42, 21); g.fill(); g.stroke(); g.restore();
        arText('واتساب', x + cw / 2, y + off + 2, 26, 700, '#fffdf8', { blur: 0 }); }
      if (i === 5) hexIcon(CX + w / 2 + 30, y + off - 4, 15, '#ffc676');
    });
  }
}

function render(t) {
  const sk = skyAt(t); cam(t);
  const night = sk.night;
  sea.U.uTime.value = t; sea.U.uAmp.value = 1 + night * .3; sea.U.uDeep.value.copy(sk.deep); sea.U.uShal.value.copy(sk.shal);
  sea.U.uFoam.value.set(night > .5 ? '#9fb0e0' : '#ffffff');
  hemi.color.copy(sk.hs); hemi.groundColor.copy(sk.hg); hemi.intensity = sk.hI;
  const se = sk.el * DEG, sa = sk.az * DEG; sun.color.copy(sk.sun); sun.intensity = sk.sunI;
  sun.target.position.set(CAM.tg[0], 0, CAM.tg[2]); sun.position.set(CAM.tg[0] + Math.cos(se) * Math.sin(sa) * 60, Math.sin(se) * 60, CAM.tg[2] + Math.cos(se) * Math.cos(sa) * 60);
  post.comp.zen.value.copy(sk.zen); post.comp.hor.value.copy(sk.hor);
  post.comp.stars.value = ss(seg(night, .3, 1)); post.comp.starOff.value = CAM.az / 60; post.comp.time.value = t;
  const gd = post.grade; gd.sat.value = lerp(1.05, 1.12, night); gd.contrast.value = lerp(.06, .12, night);
  gd.lift.value.setRGB(lerp(.018, .012, night), lerp(.016, .016, night), lerp(.024, .045, night)); gd.vig.value = lerp(.14, .3, night);
  post.bloom.strength = lerp(.22, .55, night);
  { const f = new THREE.Vector3(); camera.getWorldDirection(f); const fl = Math.hypot(f.x, f.z) || 1; sea.U.uFwd.value.set(f.x / fl, f.z / fl); sea.U.uTgt.value.set(CAM.tg[0], CAM.tg[2]); sea.U.uSpanF.value = CAM.fh / Math.tan(Math.min(80, CAM.el) * DEG) * .5; sea.U.uNight.value = night; }
  world.update(t, { night, sea, cam: camera });
  post.composer.render();
  hud(t);
}
function events() {
  const ev = world.EVS.slice();
  LINES.forEach(l => ev.push({ t: l.t0, type: 'vo', id: l.id }));
  for (const k of ['rise', 'hop1', 'arrive2', 'arrive3', 'arrive4', 'zero0', 'night', 'replay0', 'tower0', 'screen', 'end']) ev.push({ t: T[k], type: 'cue', name: k });
  return ev.sort((a, b) => a.t - b.t);
}
window.render = render; window.DUR = DUR; window.EV = events();
window.TEXTS = t => (t >= T.end + .6 ? [{ id: 'end', text: 'إشهار و حلول طباعة ذكية', x0: 200, y0: 660, x1: 800, y1: 720 }] : []);
await document.fonts.load('700 44px Cairo'); await document.fonts.load('800 50px Cairo'); await document.fonts.load('700 50px JBMono');
render(+(QS.get('t') ?? 10));
window.READY = true;
