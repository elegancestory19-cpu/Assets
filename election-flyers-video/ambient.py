"""Calm ambient bed: warm low-passed pads, slow swells, sparse soft electric-piano notes.
No percussion, no fast arpeggios, nothing above ~2 kHz. -> out/ambient.wav"""
import numpy as np, wave, os
SR, DUR = 44100, 54.0
N = int(DUR * SR)
rng = np.random.default_rng(21)
L = np.zeros(N); R = np.zeros(N)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))

def add(sig, t, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N: return
    s = sig[:N - i] * g
    L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2); R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2)

def pad(ms, dur, att=2.5, rel=2.5):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for m in ms:
        f = midi(m)
        for det, a in ((-0.03, .5), (0.03, .5)):
            ff = f * 2 ** (det / 12)
            y += a * (np.sin(2 * np.pi * ff * t + rng.uniform(0, 6.3)) + .18 * np.sin(4 * np.pi * ff * t))
    e = np.clip(t / att, 0, 1) ** 2 * np.clip((dur - t) / rel, 0, 1) ** 2
    return lowpass(y * e, 900) / len(ms)

def epiano(m, vel=.5, dur=4.0):  # soft sine-based keys, slow decay, no hammer noise
    f = midi(m); n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + .22 * np.sin(4 * np.pi * f * t) * np.exp(-t / .6) + .06 * np.sin(6 * np.pi * f * t) * np.exp(-t / .3)
    e = np.minimum(t / .03, 1) * np.exp(-t / 1.8) * np.clip((dur - t) / .8, 0, 1)
    return lowpass(y * e * vel, 1600)

def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * midi(m) * t) * np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)

# gentle progression in D major (Dmaj7 - Bm7 - Gmaj7 - A sus), one chord per scene block
SEG = [(0.0, 38, [57, 62, 66, 69]), (5.3, 38, [57, 62, 66, 73]), (11.9, 35, [54, 59, 62, 66]),
       (20.95, 43, [55, 59, 62, 66]), (28.5, 40, [55, 59, 62, 67]), (36.4, 45, [57, 61, 64, 69]),
       (42.4, 42, [54, 57, 61, 64]), (48.0, 38, [57, 62, 66, 69])]
for i, (t0, bass, ch) in enumerate(SEG):
    t1 = SEG[i + 1][0] if i + 1 < len(SEG) else DUR
    d = t1 - t0
    add(pad(ch, d + 3.0, att=2.0, rel=3.0), max(0, t0 - .8), .30)
    add(sub(bass - 12, d + 2.0), max(0, t0 - .5), .18)
    # sparse melody: one soft note at the scene start, one in the middle
    top = ch[-1] + 12
    add(epiano(top, .45, 4.5), t0 + .15, .22, .25)
    if d > 4.5: add(epiano(ch[-2] + 12, .38, 4.5), t0 + d / 2, .18, -.25)
add(epiano(78, .4, 3), 48.6, .2, .2); add(epiano(74, .35, 2.4), 49.3, .18, -.2)

def ir(seed):
    r = np.random.default_rng(seed); n = int(4.0 * SR); t = np.arange(n) / SR
    y = lowpass(r.standard_normal(n) * np.exp(-t / 1.1), 2500); y[:int(.02 * SR)] = 0
    return y / np.sqrt(np.sum(y ** 2))
def conv(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)]
oL = L * .7 + conv(L, ir(1)) * .6
oR = R * .7 + conv(R, ir(2)) * .6
for o in (oL, oR):
    o[:int(1.0 * SR)] *= np.linspace(0, 1, int(1.0 * SR)) ** 2
    o[-int(2.5 * SR):] *= np.linspace(1, 0, int(2.5 * SR)) ** 2
pk = max(np.abs(oL).max(), np.abs(oR).max()); oL /= pk / .8; oR /= pk / .8
os.makedirs('out', exist_ok=True)
with wave.open('out/ambient.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([oL, oR], 1) * 32767).astype('<i2').tobytes())
print('ok')
