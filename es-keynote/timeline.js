// timeline.js: the single source of truth (picture, score, captions, checks).
export const BPM = 120, BEAT = 0.5, BAR = 2.0, S16 = 0.125;
export const DUR = 46.0;

// key times (s)
export const K = {
  freeze: 4.0, tile: 4.1, click: 5.0, sweep0: 5.35, sweep1: 6.65, head3: 6.5,
  design: 9.5, print: 14.5, uv0: 15.0, uv1: 16.3, prod: 20.0, breath: 25.3,
  num: 25.5, dive: 27.95, facade: 28.5, signs: 29.5, sign0: 30.0, sign1: 31.2, whip: 31.5,
  digi: 33.5, snapFly: 36.55, snap: 37.0, put: 40.0, endTile: 41.25, end: 41.5,
};

// S1 storm: the beat divides 1 → 2 → 4 → 8 (one card per note)
export const STORM = [];
[[0, 1, 0.5], [1, 2, 0.25], [2, 3, 0.125], [3, 3.999, 0.0625]].forEach(([a, b, st]) => { for (let t = a; t < b - 1e-6; t += st) STORM.push(+t.toFixed(4)); });

// S4 design: tab arrivals and preview switches (beats)
export const TABS = [10.0, 10.5, 11.0, 11.5];
export const PREV = [10.0, 11.0, 12.0, 13.0];
// S5 print: material chips land on beats
export const CHIPS = [16.5, 17.0, 17.5, 18.0, 18.5];
export const CODES = 19.0;
// S6 products: three flights land on downbeats
export const LAND = [21.0, 22.0, 23.0];
export const PUTROW = [24.5, 24.75, 25.0];
// S7 number: digits lock right to left on sixteenths ("3.20": 3 . 2 0)
export const LOCKS = [26.125, 26.125, 26.0, 25.875];
// S9 digital: web blocks build on eighths
export const BLOCKS = [34.5, 34.75, 35.0, 35.25, 35.5, 35.75];
// S11 put-away: tiles retract one per eighth (11 tiles; the last one stays)
export const RETRACT = Array.from({ length: 11 }, (_, i) => +(K.put + i * 0.125).toFixed(3));

// voice-over script (client records; I only trim silences). cap: on-screen caption (null = carried by a headline, .srt only)
export const LINES = [
  { id: 'L1', t0: 0.4, t1: 3.6, say: 'لوغو هنا، طباعة لهيه، لافتة في بلاصة أخرى…', cap: [0.4, 3.6] },
  { id: 'L2', t0: 3.7, t1: 4.9, say: 'تعبت تحوّس؟', cap: [3.7, 5.5] },
  { id: 'L3', t0: 5.6, t1: 9.2, say: 'إيليغانس ستوري… حكايتك بكل أناقة.', srt: 'Elegance Story… حكايتك بكل أناقة.', cap: null },
  { id: 'L4', t0: 9.8, t1: 14.2, say: 'نبداو بالتصميم: لوغو، هوية بصرية، والألوان لي تشبهك.', cap: [9.8, 14.3] },
  { id: 'L5', t0: 14.8, t1: 19.7, say: 'نطبعو على أي سطح: زجاج، خشب، جلد، معدن… وحتى القارورات والكؤوس.', cap: [14.8, 19.8] },
  { id: 'L6', t0: 20.3, t1: 25.2, say: 'كارطات فيزيت، ستيكرز مقصوصة على القدّ، تيشرتات وكاسكيطات بشعارك.', cap: [20.3, 25.2] },
  { id: 'L7', t0: 27.0, t1: 29.4, say: 'واجهات كبيرة… حتى ثلاثة متر وعشرين.', srt: 'واجهات كبيرة… حتى 3.20 متر.', cap: [28.5, 30.25] },
  { id: 'L8', t0: 30.3, t1: 33.3, say: 'لافتات مضوّية، رول أب، وستاندات للمعارض.', cap: [30.3, 33.4] },
  { id: 'L9', t0: 33.8, t1: 36.8, say: 'وزيد: فيديوهات موشن ديزاين، ومواقع ويب.', cap: [33.8, 36.8] },
  { id: 'L10', t0: 37.4, t1: 39.8, say: 'كلّش تحت سقف واحد… في سطيف.', cap: null },
  { id: 'L11', t0: 41.8, t1: 44.8, say: 'عيّطلنا ولا ابعثلنا في الواتساب.', cap: [41.8, 45.4] },
];
