"""mix.py: score + the client's voice → out/mix.wav. No SFX (client rule).
Voice: put voice/L1.wav … voice/L11.wav (one per line), or voice/full.wav (one take; split it into lines first).
Each line is only trimmed of silence (never sped up or pitch-changed) and placed at its t0 from timeline.json.
Music ducks ≥ 12 dB under every word. Without voice files it writes a music-only preview.
"""
import os, sys, json, glob
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio.sfx import SR
from scipy.signal import resample_poly
from scipy.ndimage import maximum_filter1d, uniform_filter1d

D = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(D, 'timeline.json'))); DUR = TL['DUR']; N = int(DUR * SR)
mus, sr = sf.read(os.path.join(D, 'music/score.wav')); assert sr == SR
mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))[:N]
vox = np.zeros(N); placed = []

def load(p):
    x, r = sf.read(p); x = x.mean(1) if x.ndim > 1 else x
    if r != SR: x = resample_poly(x, SR, r)
    return x
def trim(x, db=-45, pad=0.04):
    e = uniform_filter1d(np.abs(x), int(0.01 * SR)); thr = e.max() * 10 ** (db / 20); idx = np.where(e > thr)[0]
    if not len(idx): return x
    a, b = max(0, idx[0] - int(pad * SR)), min(len(x), idx[-1] + int(pad * SR)); return x[a:b]

for L in TL['LINES']:
    p = os.path.join(D, 'voice', L['id'] + '.wav')
    if not os.path.exists(p): continue
    # already cut at true silence with soft fades: no second trim
    x = load(p); s = int(L['t0'] * SR); e = min(N, s + len(x)); vox[s:e] += x[:e - s]
    over = L['t0'] + len(x) / SR - L['t1']
    placed.append((L['id'], round(len(x) / SR, 2), round(over, 2)))

if placed:
    # no compression or EQ on the client's voice: one overall gain only
    vox = vox / (np.sqrt(np.mean(vox[np.abs(vox) > 1e-4] ** 2)) + 1e-9) * 10 ** (-18 / 20)
    # duck: music −14 dB wherever a word is (attack 40 ms, release 250 ms)
    env = maximum_filter1d((np.abs(vox) > 10 ** (-45 / 20)).astype(float), int(0.12 * SR))
    env = uniform_filter1d(env, int(0.25 * SR)); g = 10 ** (-14 * np.clip(env * 1.5, 0, 1) / 20)
    mus = mus * g[:, None] * 10 ** (-6 / 20)
    out = mus + vox[:, None]
    sp = np.abs(vox) > 10 ** (-40 / 20); vr = np.sqrt(np.mean(vox[sp] ** 2)); mr = np.sqrt(np.mean(mus[sp] ** 2))
    print(f'voice vs music while speaking: {20*np.log10(vr/mr):.1f} dB')
    for i, d, o in placed: print(f'{i}: {d}s' + (f'  ⚠ {o}s longer than its slot' if o > 0.05 else ''))
else:
    out = mus * 10 ** (-3 / 20); print('no voice files yet → music-only preview')
out = out / max(1e-9, np.abs(out).max()) * 0.9
os.makedirs(os.path.join(D, 'out'), exist_ok=True)
sf.write(os.path.join(D, 'out/mix.wav'), out.astype(np.float32), SR)
print('out/mix.wav', DUR, 's')
