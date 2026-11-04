// timeline.js: the single source of truth (picture, score, captions, checks).
export const BPM = 120, BEAT = 0.5, BAR = 2.0, S16 = 0.125;
export const DUR = 50.0;
// to fit the client's voice (take 2): the design and the print sections are one bar longer each.
// times written in the 46 s layout move +2 s from 14.5 s and +2 s more from 20 s
const SH = x => +(x + (x >= 14.5 ? 2 : 0) + (x >= 20.0 ? 2 : 0)).toFixed(4);

// key times (s)
export const K = {
  freeze: 4.0, tile: 4.1, click: 5.0, sweep0: 5.35, sweep1: 6.65, head3: 6.5,
  design: 9.5, print: 14.5, uv0: 15.0, uv1: 16.3, prod: 20.0, breath: 25.3,
  num: 25.5, dive: 27.95, facade: 28.5, signs: 29.5, sign0: 30.0, sign1: 31.2, whip: 31.5,
  digi: 33.5, snapFly: 36.55, snap: 37.0, put: 40.0, endTile: 41.25, end: 41.5,
};
for (const k in K) K[k] = SH(K[k]);

// S1 storm: the beat divides 1 → 2 → 4 → 8 (one card per note)
export const STORM = [];
[[0, 1, 0.5], [1, 2, 0.25], [2, 3, 0.125], [3, 3.999, 0.0625]].forEach(([a, b, st]) => { for (let t = a; t < b - 1e-6; t += st) STORM.push(+t.toFixed(4)); });

// S4 design: tab arrivals and preview switches (beats)
export const TABS = [10.0, 10.5, 11.0, 11.5];
export const PREV = [10.0, 11.5, 13.5, 15.0];   // on «التصميم» «هوية» «الألوان»
// S5 print: material chips land on beats
export const CHIPS = [18.5, 19.5, 20.5, 21.0, 21.5];   // on «زجاج» «خشب» «جلد» «معدن»
export const CODES = 22.5;
// S6 products: three flights land on downbeats
export const LAND = [24.5, 25.5, 27.0];      // on the words «كارطات» «ستيكرز» «تيشرتات»
export const PUTROW = [24.5, 24.75, 25.0].map(SH);
// S7 number: digits lock right to left on sixteenths ("3.20": 3 . 2 0)
export const LOCKS = [26.125, 26.125, 26.0, 25.875].map(SH);
// S9 digital: web blocks build on eighths
export const BLOCKS = [34.5, 34.75, 35.0, 35.25, 35.5, 35.75].map(SH);
// S11 put-away: tiles retract one per eighth (11 tiles; the last one stays)
export const RETRACT = Array.from({ length: 11 }, (_, i) => +(K.put + i * 0.125).toFixed(3));

// voice-over script (client records; I only trim silences). cap: on-screen caption (null = carried by a headline, .srt only)
// placed from the client's recording (voice/L*.wav); captions follow what is said
export const LINES = [
  {"id": "L1", "t0": 0.15, "t1": 4.1, "say": "لوغو هنا، أمبريسيون لهيه، لافتة في بلاصة أخرى…", "cap": [0.15, 4.1]},
  {"id": "L2", "t0": 4.15, "t1": 5.09, "say": "تعبت تحوّس؟", "cap": [4.15, 5.95]},
  {"id": "L3", "t0": 5.6, "t1": 9.54, "say": "إيليغانس ستوري… حكايتك بكل أناقة.", "srt": "Elegance Story… حكايتك بكل أناقة.", "cap": null},
  {"id": "L4", "t0": 9.65, "t1": 15.85, "say": "نبداو بالتصميم: لوغو، هوية بصرية، والألوان اللي تليق بعلامتك.", "cap": [9.65, 16.2]},
  {"id": "L5", "t0": 16.55, "t1": 23.73, "say": "نطبعو على أي سطح: زجاج، خشب، جلد، معدن… وحتى القارورات والكؤوس.", "cap": [16.55, 24.0]},
  {"id": "L6", "t0": 24.05, "t1": 29.06, "say": "كارطات فيزيت، ستيكرز مقصوصة على كيفك، تيشرتات وكاسكيطات بشعارك.", "cap": [24.05, 29.41]},
  {"id": "L7", "t0": 29.15, "t1": 32.88, "say": "واجهات كبيرة… حتى لثلاث ميطرات وعشرين.", "srt": "واجهات كبيرة… حتى لـ 3.20 متر.", "cap": [31.95, 33.7]},
  {"id": "L8", "t0": 33.6, "t1": 37.52, "say": "لافتات مضوّية، رول أب، وستاندات للمعارض.", "cap": [33.75, 37.8]},
  {"id": "L9", "t0": 37.85, "t1": 41.15, "say": "وزيد: فيديوهات موشن ديزاين، ومواقع ويب.", "cap": [37.85, 41.5]},
  {"id": "L10", "t0": 41.3, "t1": 44.13, "say": "كلّش تحت سقف واحد… في سطيف.", "cap": null},
  {"id": "L11", "t0": 45.8, "t1": 48.6, "say": "عيّطلنا ولا ابعثلنا في الواتساب.", "cap": [45.8, 48.95]},
];
