import * as T from '../timeline.js';
import { writeFileSync } from 'fs';
const out = { ...T }; writeFileSync(new URL('../timeline.json', import.meta.url), JSON.stringify(out, null, 1));
console.log('timeline.json', Object.keys(out).join(' '));
