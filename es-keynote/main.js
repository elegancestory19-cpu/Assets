import { renderFilm, loadAssets, subs, texts, events, DUR } from './film.js';
const cv = document.getElementById('c'), g = cv.getContext('2d');
await Promise.all([500, 600, 700, 800].flatMap(w => [`${w} 40px Cairo`, `${w} 40px JBMono`, `${w} 40px InterTight`]).map(f => document.fonts.load(f, 'abc 0123 كلّش')));
await loadAssets();
window.DUR = DUR; window.EV = events(); window.SUBS = subs(); window.TEXTS = texts;
const Q = new URLSearchParams(location.search);
window.render = t => renderFilm(g, t, { nosub: Q.has('nosub') });
window.READY = true;
