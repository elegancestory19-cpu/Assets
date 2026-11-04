// world.js: five service islands + a tower islet, props, the idea cube, growth schedule (events carry notes)
import * as THREE from 'three';
import { clamp, seg, ss, eo, ei, eio, lerp, hash, TAU } from '/core/lib.js';
import { T, note } from './story.js';
import { waveH } from './sea.js';

const SQ3 = Math.sqrt(3), R = 0.55;                    // tile circumradius
const hexXY = (q, r) => [SQ3 * R * (q + r / 2), 1.5 * R * r];
const hd = (q, r) => Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r));

// ── materials (flat, no textures except the official logo prints)
const MC = new Map();
export function mat(hex, o = {}) {
  const k = hex + JSON.stringify(o);
  if (!MC.has(k)) MC.set(k, new THREE.MeshStandardMaterial({ color: hex, flatShading: true, roughness: .88, metalness: 0, ...o }));
  return MC.get(k);
}
const jit = (hex, a) => { const c = new THREE.Color(hex), h = {}; c.getHSL(h); c.setHSL(h.h, h.s, clamp(h.l * (1 + a))); return '#' + c.getHexString(); };
const at = (o, x, y, z) => { o.position.set(x, y, z); return o; };
const M = (g, m, cast = true) => { const x = new THREE.Mesh(g, m); x.castShadow = cast; x.receiveShadow = true; return x; };

export const PAL = {
  sandTop: '#f3dfab', sandSide: '#e2c68e', grassTop: '#a8d8a0', grassTop2: '#95cc8e', earth: '#c9a27a', stone: '#e6ddd0', stoneSide: '#bfb3a3',
  // brand colours softened to pastel (cyan, blue, purple, magenta, orange, yellow)
  walls: ['#bfeef6', '#bccdf2', '#d9c6ee', '#f2c6e4', '#f6d2b0', '#f8e7b0', '#fbf3e6'],
  roofs: ['#2aa9c0', '#4a6fd0', '#8a5cc0', '#c95aa8', '#e08a3e', '#e8b83e'],
  leaf: ['#7fc36a', '#9ad06f'], trunk: '#8a5a3c', dark: '#3a3f4c', metal: '#b9c0c8', wood: '#c99c6e', glass: '#cfeef4',
  warm: '#ffc676', cyan: '#1CCEE9',
};

// ── arrival curves (s = t − event time; the event time is when it settles)
const riseY = s => s < -0.5 ? null : s < 0 ? -2.6 * Math.pow(1 - eo((s + .5) / .5), 1) : Math.sin(13 * s) * Math.exp(-7 * s) * .12;
const dropY = s => s < -0.22 ? null : s < 0 ? 2.2 * (1 - ei((s + .22) / .22)) : Math.abs(Math.sin(15 * s)) * Math.exp(-9 * s) * .18;
const squash = s => s < 0 ? 1 : 1 - .16 * Math.exp(-12 * s) * Math.cos(26 * s);
const popS = s => s < 0 ? 0 : Math.max(0, 1 - Math.exp(-9 * s) * Math.cos(17 * s));

// ── layout: island centres (world x, z). Final view is top-down with screen up = −z
export const ISL = {
  start: [-4.6, -9.6], i1: [-3.2, -6.0], i2: [3.2, -5.0], i3: [3.4, 3.2], i4: [-3.2, 4.4], c: [0, -.4],
};
function cluster(cx, cz, rad, skip = []) {
  const out = [];
  for (let q = -rad; q <= rad; q++) for (let r = -rad; r <= rad; r++) {
    const d = hd(q, r); if (d > rad || skip.includes(q + ',' + r)) continue;
    const [x, z] = hexXY(q, r); out.push({ q, r, d, x: cx + x, z: cz + z });
  }
  return out;
}

export function buildWorld(scene, tex) {
  const EVS = [], upd = [], blobs = [];
  const ev = (t, type, n, extra = {}) => { EVS.push({ t: +t.toFixed(4), type, note: n, ...extra }); };
  const root = new THREE.Group(); scene.add(root);

  // printable logo material (the official artwork, unchanged)
  const logoMat = (which = 'tag', emissive = 0) => new THREE.MeshStandardMaterial({ map: tex[which], roughness: .55, metalness: 0, emissive: emissive ? '#ffffff' : '#000000', emissiveMap: emissive ? tex[which] : null, emissiveIntensity: emissive });

  // ── hex tiles
  function tile(x, z, h, top, side, tRise, n, o = {}) {
    const g = new THREE.Group(); g.position.set(x, 0, z);
    const r = o.r ?? R;
    const body = M(new THREE.CylinderGeometry(r * .97, r * .97, h - .1 + 2.4, 6), mat(side), false); body.position.y = (h - .1 - 2.4) / 2; g.add(body);
    const cap = M(new THREE.CylinderGeometry(r * .985, r * .985, .16, 6), o.capMat || mat(top)); cap.position.y = h - .08; g.add(cap);
    root.add(g);
    if (n != null) ev(tRise, 'tile', n);
    const it = { g, cap, x, z, h, r, tRise };
    upd.push(t => { const y = riseY(t - tRise); g.visible = y !== null; if (g.visible) g.position.y = y; });
    blobs.push(t => [x, z, r * 2.3, ss(seg(t, tRise - .3, tRise + .2))]);
    return it;
  }
  function island(key, rad, tStart, step, topCol, h0, noteBase, skip = [], silent = false) {
    const [cx, cz] = ISL[key];
    const cs = cluster(cx, cz, rad, skip).sort((a, b) => a.d - b.d || Math.atan2(a.z - cz, a.x - cx) - Math.atan2(b.z - cz, b.x - cx));
    return cs.map((c, i) => {
      const edge = c.d === rad, top = edge ? PAL.sandTop : jit(topCol, (hash(c.x * 7 + c.z * 3) - .5) * .08);
      const h = edge ? h0 * .62 : h0 + (hash(c.x * 13 + c.z) > .6 ? .08 : 0);
      return tile(c.x, c.z, h, top, edge ? PAL.sandSide : PAL.earth, tStart + i * step, silent ? null : note(noteBase + i));
    });
  }
  function bridge(a, b, tStart, step, n0, ra = 1.15, rb = 1.15, count = null) {
    const [ax, az] = ISL[a], [bx, bz] = ISL[b], dx = bx - ax, dz = bz - az, L = Math.hypot(dx, dz);
    const s0 = ra, s1 = L - rb, k = count ?? Math.max(3, Math.round((s1 - s0) / .62));
    const out = [];
    for (let i = 0; i < k; i++) {
      const u = (s0 + (s1 - s0) * (i + .5) / k) / L;
      out.push(tile(ax + dx * u, az + dz * u, .34, '#f6e9c6', PAL.sandSide, tStart + i * step, note(n0 + i), { r: .3 }));
    }
    return out;
  }

  // ── props
  const box = (w, h, d, c, o) => M(new THREE.BoxGeometry(w, h, d), typeof c === 'string' ? mat(c, o) : c);
  function prism(w, d, h, c) {   // gable roof
    const g = new THREE.BufferGeometry(), W = w / 2 + .05, D = d / 2 + .05;
    const v = [-W, 0, -D, W, h, 0, W, 0, -D, -W, 0, -D, -W, h, 0, W, h, 0, -W, 0, D, W, h, 0, -W, h, 0, -W, 0, D, W, 0, D, W, h, 0,
      -W, 0, -D, W, 0, D, -W, 0, D, -W, 0, -D, W, 0, -D, W, 0, D, W, 0, -D, W, h, 0, W, 0, D, -W, 0, D, -W, h, 0, -W, 0, -D];
    g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.computeVertexNormals();
    return M(g, mat(c));
  }
  function place(obj, x, y, z, ry = 0) { obj.position.set(x, y, z); obj.rotation.y = ry; root.add(obj); return obj; }
  const winMats = [];
  function windowMat() { const m = new THREE.MeshStandardMaterial({ color: '#4d5c74', emissive: PAL.warm, emissiveIntensity: 0, flatShading: true, roughness: .5 }); winMats.push(m); return m; }
  function popper(obj, t0, n, kind = 'pop') {   // animate an object in with pop or drop
    const base = obj.position.y, s0 = obj.scale.clone();
    if (n != null) ev(t0, kind, n);
    upd.push(t => {
      const s = t - t0;
      if (kind === 'drop') { const y = dropY(s); obj.visible = y !== null; if (!obj.visible) return; obj.position.y = base + y; const q = squash(s); obj.scale.set(s0.x / Math.sqrt(q), s0.y * q, s0.z / Math.sqrt(q)); }
      else { const k = popS(s); obj.visible = k > 0.001; obj.scale.copy(s0).multiplyScalar(Math.max(k, .001)); }
    });
    return obj;
  }
  function house(x, z, y0, floors, wi, ri, t0, n, ry = 0, o = {}) {
    const g = new THREE.Group(); place(g, x, y0, z, ry);
    const W = o.w ?? .62, D = o.d ?? .62, FH = o.fh ?? .42, wm = windowMat();
    for (let f = 0; f < floors; f++) {
      const fl = new THREE.Group(); fl.position.y = f * FH;
      fl.add(at(box(W, FH, D, PAL.walls[wi % 7]), 0, FH / 2, 0));
      for (let s = 0; s < 2; s++) { const wq = new THREE.Mesh(new THREE.PlaneGeometry(.12, .16), wm); wq.position.set((s - .5) * W * .5, FH * .55, D / 2 + .005); fl.add(wq);
        const wq2 = wq.clone(); wq2.rotation.y = Math.PI / 2; wq2.position.set(W / 2 + .005, FH * .55, (s - .5) * D * .5); fl.add(wq2); }
      g.add(fl); popper(fl, t0 + f * .25, n != null ? note(n + f) : null, 'drop');
    }
    const roof = prism(W, D, .3, PAL.roofs[ri % 6]); roof.position.y = floors * FH; g.add(roof); popper(roof, t0 + floors * .25, n != null ? note(n + floors + 2) : null, 'drop');
    return { g, wm };
  }
  function tree(x, z, y0, t0, n, k = 0) {
    const g = new THREE.Group(); place(g, x, y0, z);
    const tr = box(.06, .22, .06, PAL.trunk); tr.position.y = .11; g.add(tr);
    const cr = M(new THREE.IcosahedronGeometry(.2, 0), mat(PAL.leaf[k % 2])); cr.position.y = .34; g.add(cr);
    popper(g, t0, n);
  }
  const top = (it) => it.h;   // tile top height

  // ═════ the idea cube
  const cubeMat = new THREE.MeshStandardMaterial({ color: PAL.cyan, emissive: PAL.cyan, emissiveIntensity: 1.4, flatShading: true, roughness: .4 });
  const cube = M(new THREE.BoxGeometry(.32, .32, .32), cubeMat); root.add(cube);
  ev(T.rise, 'motif', 86);

  // ═════ islands
  const I1 = island('i1', 1, T.i1, .25, PAL.grassTop, .62, 0);
  const B1 = bridge('i1', 'i2', T.b1, .125, 3, 1.0, 1.0, 7);
  const I2 = island('i2', 1, T.i2, .125, '#e6ddd0', .62, 5);
  const B2 = bridge('i2', 'i3', T.b2, .125, 4, 1.0, 1.0, 9);
  const I3 = island('i3', 1, T.b2 + .5, .125, PAL.grassTop2, .62, 7, [], true);
  const B3 = bridge('i3', 'i4', T.b3, .125, 2, 1.0, 1.75, 6);
  const I4 = island('i4', 2, T.b3 + .25, .0625, PAL.grassTop, .62, 0, ['2,-2', '-2,2', '2,0'], true);
  const C = island('c', 1, T.tower0 - .75, .125, PAL.stone, .7, 3);

  // ═════ 1 design studio
  const [x1, z1] = ISL.i1, y1 = .62;
  const st = house(x1 + .2, z1 - .15, y1, 1, 2, 2, T.studio, 1, .3, { w: .9, d: .7, fh: .5 });
  const board = new THREE.Group(); place(board, x1 - .45, y1, z1 + .35, .5);
  board.add(at(box(.03, .5, .03, PAL.trunk), 0, .25, -.08));
  const bp = M(new THREE.BoxGeometry(.5, .5, .03), mat('#fbf3e6')); bp.position.set(0, .48, 0); bp.rotation.x = -.18; board.add(bp);
  const bl = new THREE.Mesh(new THREE.PlaneGeometry(.44, .44), logoMat('logo3d')); bl.position.set(0, .48, .02); bl.rotation.x = -.18; board.add(bl);
  popper(board, T.board, 81);
  ['#1CCEE9', '#2457D6', '#8844C0', '#DA43AE', '#E57E22'].forEach((c, i) => {   // colour swatches fanning out
    const sw = box(.08, .015, .34, c); sw.geometry.translate(0, 0, .15); place(sw, x1 + .5, y1 + .02 + i * .016, z1 + .45, -.9 + i * .32);
    popper(sw, T.swatch + i * .25, note(4 + i));
  });
  tree(x1 - .6, z1 - .5, y1, T.trees1, note(2)); tree(x1 + .65, z1 - .55, y1, T.trees1 + .25, note(5), 1);

  // ═════ 2 UV flatbed + glass / wood / metal panels
  const [x2, z2] = ISL.i2, y2 = .62;
  const tableG = new THREE.Group(); place(tableG, x2, y2, z2, .35);
  tableG.add(at(box(1.5, .32, .8, PAL.dark), 0, .16, 0));
  tableG.add(at(box(1.42, .02, .72, '#4a5060'), 0, .33, 0));
  popper(tableG, T.table, note(5), 'drop');
  const gantry = new THREE.Group(); tableG.add(gantry);
  [-1, 1].forEach(s => gantry.add(at(box(.08, .34, .08, '#5a6070'), 0, .5, s * .42)));
  gantry.add(at(box(.14, .1, .92, '#6a7080'), 0, .68, 0));
  const lampMat = new THREE.MeshStandardMaterial({ color: '#8a7cff', emissive: '#7a6cff', emissiveIntensity: 0, roughness: .4 });
  const lamp = M(new THREE.BoxGeometry(.06, .03, .74), lampMat, false); lamp.position.set(0, .6, 0); gantry.add(lamp);
  popper(gantry, T.gantry, note(7), 'drop');
  const PAN = [{ c: PAL.glass, o: { roughness: .15, metalness: .1 } }, { c: PAL.wood, o: {} }, { c: PAL.metal, o: { metalness: .55, roughness: .35 } }];
  const prints = PAN.map((p, i) => {
    const px = -.45 + i * .45, pan = box(.36, .03, .5, p.c, p.o); pan.position.set(px, .355, 0); tableG.add(pan); popper(pan, T.panels[i], note(6 + i));
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(.3, .3), logoMat('tag')); pl.rotation.x = -Math.PI / 2; pl.position.set(px, .372, 0); tableG.add(pl);
    popper(pl, T.prints[i], note(9 + i));
    return { px, pl };
  });
  upd.push(t => {   // lamp travels across the bed between lamp0 and lamp1, passing each panel on its print time
    const xs = prints.map(p => p.px), ts = T.prints;
    let gx = -.75;
    if (t < T.lamp0) gx = -.75; else if (t < ts[0]) gx = lerp(-.75, xs[0], ss(seg(t, T.lamp0, ts[0])));
    else if (t < ts[1]) gx = lerp(xs[0], xs[1], ss(seg(t, ts[0], ts[1]))); else if (t < ts[2]) gx = lerp(xs[1], xs[2], ss(seg(t, ts[1], ts[2])));
    else gx = lerp(xs[2], .75, ss(seg(t, ts[2], T.lamp1)));
    gantry.position.x = gx; lampMat.emissiveIntensity = t > T.lamp0 - .2 && t < T.lamp1 + .1 ? 3.2 : 0;
  });

  // ═════ 3 gifts: heat press + T-shirt, cap, mug
  const [x3, z3] = ISL.i3, y3 = .62;
  const press = new THREE.Group(); place(press, x3 - .42, y3, z3 + .12, -.4);
  press.add(at(box(.6, .1, .5, '#c9ced6'), 0, .05, 0));
  press.add(at(box(.08, .5, .08, '#5a6070'), -.28, .3, 0));
  const lid = new THREE.Group(); lid.position.set(-.28, .5, 0); press.add(lid);
  lid.add(at(box(.6, .07, .5, PAL.metal, { metalness: .5, roughness: .35 }), .3, 0, 0));
  popper(press, T.press, note(4), 'drop');
  ev(T.lid, 'press', 62);
  upd.push(t => { const a = t < T.lid - .25 ? .9 : t < T.lid ? lerp(.9, 0, ei(seg(t, T.lid - .25, T.lid))) : t < T.lift ? 0 : lerp(0, .9, eo(seg(t, T.lift, T.lift + .3))); lid.rotation.z = a; });
  // T-shirt (flat extruded silhouette), black, with the logo
  const sh = new THREE.Shape(); sh.moveTo(-.12, -.2); sh.lineTo(.12, -.2); sh.lineTo(.12, .08); sh.lineTo(.2, .03); sh.lineTo(.24, .1); sh.lineTo(.12, .2); sh.lineTo(.05, .2);
  sh.quadraticCurveTo(0, .15, -.05, .2); sh.lineTo(-.12, .2); sh.lineTo(-.24, .1); sh.lineTo(-.2, .03); sh.lineTo(-.12, .08); sh.closePath();
  const shirtG = new THREE.Group(); place(shirtG, x3 - .42, y3 + .11, z3 + .12, -.4);
  const shirt = M(new THREE.ExtrudeGeometry(sh, { depth: .02, bevelEnabled: false }), mat('#22252d')); shirt.rotation.x = -Math.PI / 2; shirtG.add(shirt); shirtG.scale.setScalar(1.25);
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(.17, .17), logoMat('logo3d')); sl.rotation.x = -Math.PI / 2; sl.position.y = .025; shirtG.add(sl);
  popper(shirtG, T.gifts[0], note(8));
  const cap = new THREE.Group(); place(cap, x3 + .42, y3, z3 - .38, .6);
  cap.add(at(M(new THREE.SphereGeometry(.15, 7, 4, 0, TAU, 0, Math.PI / 2), mat('#22252d')), 0, .0, 0));
  cap.add(at(M(new THREE.CylinderGeometry(.13, .13, .015, 7, 1, false, -.9, 1.8), mat('#22252d')), 0, .01, .12));
  const cl = new THREE.Mesh(new THREE.PlaneGeometry(.1, .1), logoMat('logo3d')); cl.position.set(0, .07, .13); cl.rotation.x = -.5; cap.add(cl);
  popper(cap, T.gifts[1], note(9));
  const mug = new THREE.Group(); place(mug, x3 + .38, y3, z3 + .42, -.5);
  mug.add(at(M(new THREE.CylinderGeometry(.1, .1, .22, 10), mat('#fbfbf8')), 0, .11, 0));
  mug.add(at(M(new THREE.TorusGeometry(.06, .015, 4, 8), mat('#fbfbf8')), .11, .12, 0));
  const ml = new THREE.Mesh(new THREE.PlaneGeometry(.14, .14), logoMat('logo3d')); ml.position.set(0, .11, .102); mug.add(ml);
  popper(mug, T.gifts[2], note(10));
  tree(x3 + .1, z3 + .6, y3, T.b2 + 1.0, null, 1);

  // ═════ 4 facade: a building stacks, the banner grows to 3.20 m, the shop's sign lights at dusk, a roll-up
  const [x4, z4] = ISL.i4, y4 = .62;
  const bld = house(x4 + .1, z4 - .2, y4, 4, 6, 1, T.floors[0], 3, 2.44, { w: 1.1, d: .8, fh: .42 });
  // replace stagger: floors on T.floors handled by house() (0.25 s apart)
  const banner = new THREE.Mesh(new THREE.PlaneGeometry(.84, 1.3), logoMat('logo3d', .15));
  banner.geometry.translate(0, .65, 0); const bannerG = new THREE.Group(); place(bannerG, x4 + .1, y4 + .15, z4 - .2, 2.44);
  banner.position.set(0, 0, .405); bannerG.add(banner);
  ev(T.banner1, 'banner', 69);
  upd.push(t => { const k = eo(seg(t, T.banner0, T.banner1)); banner.visible = k > .01; banner.scale.y = Math.max(k, .01); });
  const shop = house(x4 - .9, z4 + .55, y4, 1, 4, 3, T.floors[0] - .5, null, 2.44, { w: .8, d: .6, fh: .45 });
  const signMat = logoMat('tag', 0); signMat.emissive.set('#ffffff'); signMat.emissiveMap = tex.tag;
  const sign = box(.5, .22, .06, mat('#22252d')); const signFace = new THREE.Mesh(new THREE.PlaneGeometry(.46, .2), signMat); signFace.position.z = .031; sign.add(signFace);
  place(sign, x4 - .9 + Math.sin(2.44) * .33, y4 + .62, z4 + .55 + Math.cos(2.44) * .33, 2.44);
  popper(sign, T.floors[0], null);
  ev(T.sign, 'sign', 74);
  upd.push(t => { signMat.emissiveIntensity = t < T.sign ? .0 : lerp(0, 1.3, ss(seg(t, T.sign, T.sign + .3))); });
  const roll = new THREE.Group(); place(roll, x4 - .2, y4, z4 + .1, 2.44);
  roll.add(at(box(.3, .04, .08, PAL.metal), 0, .02, 0));
  const rp = new THREE.Mesh(new THREE.PlaneGeometry(.28, .62), logoMat('logo3d')); rp.position.set(0, .35, .0); roll.add(rp);
  const rpb = rp.clone(); rpb.rotation.y = Math.PI; rpb.material = mat('#22252d'); roll.add(rpb);
  popper(roll, T.rollup, note(9));
  tree(x4 + 1.0, z4 + .8, y4, T.b3 + 1.0, null); tree(x4 - 1.1, z4 - .7, y4, T.b3 + 1.2, null, 1);
  const extra = [house(x4 + 1.1, z4 - .9, y4, 2, 0, 0, T.b3 + 1.1, null, .9), house(x2 - .9, z2 + .7, y2, 1, 5, 4, T.i2 + .9, null, .4)];

  // ═════ C tower with the logo screen
  const [xc, zc] = ISL.c, yc = .7;
  const tower = new THREE.Group(); place(tower, xc, yc, zc, Math.PI / 4);
  const tw = [box(.7, .5, .7, PAL.walls[6]), box(.6, .5, .6, PAL.walls[0]), box(.5, .5, .5, PAL.walls[6])];
  tw.forEach((b, i) => { b.position.y = .25 + i * .5; tower.add(b); popper(b, T.tower0 + i * .25, note(5 + i * 2), 'drop'); });
  const scrMat = logoMat('logo3d', 0); scrMat.emissive.set('#ffffff'); scrMat.emissiveMap = tex.logo3d;
  const scr = new THREE.Group(); scr.position.set(xc, yc + 1.55, zc); root.add(scr);
  scr.add(at(box(.1, 1.0, .1, PAL.metal), 0, .0, 0));
  const screenBox = box(1.7, 1.7, .1, mat('#1a1d24')); screenBox.position.y = 1.35; scr.add(screenBox);
  const sf = new THREE.Mesh(new THREE.PlaneGeometry(1.62, 1.62), scrMat); sf.position.set(0, 1.35, .051); scr.add(sf);
  popper(scr, T.tower0 + .75, note(9), 'drop');
  ev(T.screen, 'screen', 74);
  upd.push(t => { scrMat.emissiveIntensity = t < T.screen ? .05 : lerp(.05, 1.25, ss(seg(t, T.screen, T.screen + .4))); });

  // ═════ the idea's path (for the cube and the replay)
  const P = [];   // [t, x, y, z]
  const S0 = ISL.start;
  P.push([0, S0[0], -1, S0[1]], [T.rise, S0[0], .25, S0[1]], [T.hop1 - .5, S0[0], .25, S0[1]]);
  const onTile = (it, t) => P.push([t, it.x, it.h + .16, it.z]);
  onTile(I1[4], T.hop1);
  B1.forEach((b, i) => onTile(b, T.b1 + .35 + i * .19));
  onTile(I2[4], T.arrive2);
  B2.forEach((b, i) => onTile(b, T.b2 + .2 + i * .09));
  onTile(I3[0], T.arrive3); onTile(I3[5], T.arrive3 + .4);
  B3.forEach((b, i) => onTile(b, T.b3 + .2 + i * .12));
  onTile(I4[0], T.arrive4); onTile(I4[10], T.arrive4 + .45);
  P.push([T.tower0 - .3, I4[10].x, I4[10].h + .16, I4[10].z], [T.screen - .05, xc, yc + 3.25, zc], [40, xc, yc + 3.25, zc]);
  function cubeAt(t) {
    let i = 0; while (i < P.length - 2 && t > P[i + 1][0]) i++;
    const a = P[i], b = P[i + 1], u = clamp((t - a[0]) / Math.max(1e-3, b[0] - a[0]));
    const d = Math.hypot(b[1] - a[1], b[3] - a[3]), hop = d > .05 ? Math.sin(Math.PI * u) * Math.min(.8, .25 + d * .18) : 0;
    const e = d > .05 ? eio(u) : u;
    return [lerp(a[1], b[1], e), lerp(a[2], b[2], e) + hop, lerp(a[3], b[3], e)];
  }
  // the replay: the path lights up in travel order (each tile was a note; now it glows again on it)
  const pathTiles = [I1[4], ...B1, I2[4], ...B2, I3[0], ...B3, I4[0]];
  const glowMat = new THREE.MeshStandardMaterial({ color: '#f6e9c6', emissive: PAL.cyan, emissiveIntensity: 0, flatShading: true, roughness: .8 });
  pathTiles.forEach((it, i) => {
    const tg = T.replay0 + i * (1.6 / pathTiles.length); const m = glowMat.clone(); const orig = it.cap.material;
    ev(tg, 'replay', note(i));
    upd.push(t => { if (t < tg) { it.cap.material = orig; return; } it.cap.material = m; m.emissiveIntensity = lerp(1.6, .55, ss(seg(t, tg, tg + .6))); });
  });
  // windows light at night, one per note after the replay
  winMats.forEach((m, i) => { const tw0 = T.replay0 + .2 + i * .1; ev(tw0, 'window', null); upd.push(t => { m.emissiveIntensity = t < tw0 ? 0 : lerp(0, 1.3, ss(seg(t, tw0, tw0 + .25))); }); });
  winMats.forEach((m, i) => { if (i === 0) {} });

  return {
    EVS, ISL,
    cubeAt,
    update(t, ctx) {
      for (const f of upd) f(t);
      const [cx, cy, cz] = cubeAt(t); cube.position.set(cx, cy + (t < T.hop1 - .5 ? waveH(cx, cz, t) * .5 : 0), cz);
      cube.rotation.y = t * 1.2; cube.rotation.x = Math.sin(t * 1.7) * .25;
      const s = t < T.rise - .5 ? 0 : t < T.rise ? eo(seg(t, T.rise - .5, T.rise)) : 1; cube.scale.setScalar(Math.max(s, .001));
      cubeMat.emissiveIntensity = lerp(1.4, 2.6, ctx.night);
      if (ctx.cam) { scr.quaternion.copy(ctx.cam.quaternion); }
      if (ctx.sea) ctx.sea.drawShallow(blobs.map(f => f(t)));
    },
  };
}
