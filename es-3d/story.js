// story.js: the timeline (single source of truth for picture, score, captions)
export const BPM = 120, BEAT = 0.5, E8 = 0.25, S16 = 0.125;
export const DUR = 35.5;

// D major pentatonic (D E F# A B) — any order stays consonant
const PENT = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86, 88];
export const note = (i) => PENT[((i % PENT.length) + PENT.length) % PENT.length];

// key times: laid out on the client's recording (voice/L*.wav), beats on the spoken words
export const T = {
  rise: 1.0, tilt0: 0.4, tilt1: 2.9,
  // design island («لوغو» 5.37, «هوية» 6.1)
  i1: 3.0, hop1: 4.75, studio: 5.0, roof: 5.25, board: 5.5, swatch: 6.0, trees1: 7.0,
  // bridge + print island («زجاج» 11.26, «خشب» 12.25, «معدن» 13.2)
  b1: 7.5, i2: 7.75, arrive2: 9.0, table: 9.25, gantry: 9.5, panels: [9.75, 10.0, 10.25], lamp0: 10.75, lamp1: 13.5, prints: [11.25, 12.25, 13.25],
  // bridge + gifts island («تيشرتات» 15.03, «كاسكيطات» 16.12, «كؤوس» 17.26)
  b2: 13.5, arrive3: 14.5, press: 14.5, lid: 14.75, lift: 15.0, gifts: [15.0, 16.125, 17.25],
  // bridge + facade island («3.20» ≈ 20.5, «لافتات» 22.41)
  b3: 18.5, arrive4: 19.5, floors: [19.5, 19.75, 20.0, 20.25], bRoof: 20.5, banner0: 20.25, banner1: 21.0, sign: 22.5, rollup: 23.0,
  // night: zero, path replay, tower, logo screen («إيليغانس ستوري» 27.4)
  zero0: 24.25, night: 24.5, replay0: 24.75, tower0: 26.5, screen: 27.5,
  end: 31.0,
};
// time of day (t, zenith, horizon, deep, shallow, sun colour, sun I, hemi sky, hemi ground, hemi I, sun elev°, sun az°, night)
export const SKY = [
  [0.0, '#a9b9d6', '#f6d6c8', '#5a95ad', '#9fd3cc', '#ffd9b8', 1.6, '#f3e6ea', '#c9b8a6', 1.0, 12, 120, 0],
  [4.0, '#88c8e8', '#eaf5f2', '#38a5bc', '#86e2d4', '#fff6e8', 2.6, '#eef6fb', '#c6b89c', 1.1, 48, 150, 0],
  [17.0, '#8cc4e6', '#f2f1e6', '#3aa0b8', '#8ae0d2', '#fff0dc', 2.5, '#eef4f8', '#c8b89c', 1.05, 40, 200, 0],
  [21.0, '#8a86c0', '#ffc39e', '#4f86a8', '#a8c8c0', '#ffb07a', 2.0, '#f4dcd6', '#b8a090', .9, 16, 235, .1],
  [23.5, '#5a5a9a', '#ff9f88', '#4a5a90', '#8a86a8', '#ff8a60', 1.2, '#c8b8d8', '#8a7890', .6, 6, 245, .45],
  [24.5, '#141a40', '#4a4478', '#23264a', '#363a66', '#a9b0e8', .7, '#4a5090', '#2a2840', .55, 30, 250, 1],
  [36.0, '#121638', '#4a4478', '#23264a', '#363a66', '#a9b0e8', .7, '#4a5090', '#2a2840', .55, 30, 250, 1],
];
// voice-over: the client's recording, cut at true silence (voice/L*.wav); t1 = t0 + line length
export const LINES = [
  { id: 'L1', t0: 0.55, len: 0.99, say: 'عندك فكرة؟' },
  { id: 'L2', t0: 4.0, len: 3.34, say: 'نصمّموهالك: لوغو، وهوية كاملة.' },
  { id: 'L3', t0: 9.0, len: 4.68, say: 'نطبعوها على أي سطح… زجاج، خشب، معدن.' },
  { id: 'L4', t0: 15.0, len: 3.97, say: 'تيشرتات، كاسكيطات، كؤوس… بشعارك.' },
  { id: 'L5', t0: 19.6, len: 4.18, say: 'واجهات حتى ثلاثة متر وعشرين… ولافتات تضوّي في الليل.', srt: 'واجهات حتى 3.20 متر… ولافتات تضوّي في الليل.' },
  { id: 'L6', t0: 27.4, len: 3.30, say: 'إيليغانس ستوري… كلّش تحت سقف واحد، في سطيف.', srt: 'Elegance Story… كلّش تحت سقف واحد، في سطيف.' },
  { id: 'L7', t0: 31.5, len: 2.19, say: 'عيّطلنا ولا ابعثلنا في الواتساب.' },
];
for (const L of LINES) L.t1 = +(L.t0 + L.len).toFixed(2);
for (const L of LINES) if (!L.cap) L.cap = [L.t0 - 0.05, Math.max(L.t1 + 0.6, L.t0 + 1.8)];
for (let i = 0; i + 1 < LINES.length; i++) LINES[i].cap[1] = Math.min(LINES[i].cap[1], LINES[i + 1].cap[0] - 0.05);
