import * as S from '../story.js';
import { writeFileSync } from 'fs';
writeFileSync(new URL('../timeline.json', import.meta.url), JSON.stringify({ DUR: S.DUR, T: S.T, LINES: S.LINES }, null, 1));
const cues = S.LINES.map(L => ({ t0: L.cap[0], t1: L.cap[1], text: L.srt || L.say }));
writeFileSync(new URL('../out/srt.json', import.meta.url), JSON.stringify(cues));
console.log('timeline.json + out/srt.json');
