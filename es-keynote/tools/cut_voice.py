"""Cut one voice take into lines at true silence. No processing: no speed, pitch, EQ or compression change.
Usage: python -I tools/cut_voice.py voice/raw/<take>.wav voice/cuts.json
cuts.json = [[start, end], ...] rough speech bounds per line (from pauses + speech-to-text).
Each cut walks outward to ≥ 25 ms of real quiet (−52 dB below the take's peak), never past the midpoint
to the neighbouring line, adds 30 ms, and gets 20 ms soft fades. Writes voice/L1.wav… and voice/dur.json.
"""
import sys, json, numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d
src, cuts = sys.argv[1], json.load(open(sys.argv[2]))
x, sr = sf.read(src); x = x.mean(1) if x.ndim > 1 else x
q = 20 * np.log10(uniform_filter1d(np.abs(x), int(0.01 * sr)) + 1e-9); q -= q.max()
SIL, n25 = -52, int(0.025 * sr)
def quiet(i, step):
    run = 0
    while 0 < i < len(q) - 1:
        run = run + 1 if q[i] < SIL else 0
        if run >= n25: return i - step * n25
        i += step
    return i
out = {}
for k, (a, b) in enumerate(cuts):
    lo = (cuts[k - 1][1] + a) / 2 if k else 0.0
    hi = (b + cuts[k + 1][0]) / 2 if k < len(cuts) - 1 else len(x) / sr
    s = max(int(lo * sr), quiet(int(a * sr), -1) - int(0.03 * sr), 0)
    t = min(int(hi * sr), quiet(int(b * sr), +1) + int(0.03 * sr), len(x))
    y = x[s:t].copy(); f = int(0.02 * sr); y[:f] *= np.linspace(0, 1, f) ** 2; y[-f:] *= np.linspace(1, 0, f) ** 2
    sf.write(f'voice/L{k + 1}.wav', y, sr); out[f'L{k + 1}'] = round(len(y) / sr, 3)
    edge = lambda z: 20 * np.log10(np.sqrt(np.mean(z ** 2)) + 1e-9)
    print(f'L{k + 1}: {s / sr:6.2f} → {t / sr:6.2f}  ({len(y) / sr:.2f} s)  edges {edge(x[s:s + n25]) - 20 * np.log10(np.abs(x).max()):.0f} / {edge(x[t - n25:t]) - 20 * np.log10(np.abs(x).max()):.0f} dB')
json.dump(out, open('voice/dur.json', 'w'))
