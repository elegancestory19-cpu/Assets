"""Soft felt-piano + warm pad score, chords change on each scene cut. No drums. -> out/music.wav"""
import numpy as np, wave, os
SR, DUR = 44100, 37.4
N = int(DUR * SR)
rng = np.random.default_rng(3)
L = np.zeros(N); R = np.zeros(N)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))

def add(sig, t, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N: return
    s = sig[:N - i] * g
    L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2); R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2)

def piano(m, vel=.6, dur=2.5):
    f0 = midi(m); n = int((dur + .6) * SR); t = np.arange(n) / SR
    y = np.zeros(n); Bc = .00035
    for k in range(1, 10):
        fk = k * f0 * np.sqrt(1 + Bc * k * k)
        if fk > 9000: break
        a = vel ** (.6 + .18 * k) / k ** 1.15
        tau = 3.2 / (1 + .55 * k) * (262 / f0) ** .35
        y += a * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * np.exp(-t / tau)
    y *= np.minimum(t / .005, 1)
    h = int(.012 * SR); y[:h] += rng.standard_normal(h) * np.exp(-np.arange(h) / (.002 * SR)) * .04 * vel
    rel = np.clip((dur + .6 - t) / .6, 0, 1); y *= rel
    return lowpass(y, 1800 + 2600 * vel)

def pad(ms, dur):
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for m in ms:
        for det in (-0.07, 0.0, 0.06):
            f = midi(m) * 2 ** (det / 12)
            y += np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) + .25 * np.sin(4 * np.pi * f * t)
    e = np.minimum(t / 1.6, 1) * np.minimum((dur - t) / 1.2, 1)
    return lowpass(y * e, 1100) / (len(ms) * 3)

def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * midi(m) * t) * np.minimum(t / .08, 1) * np.exp(-t / 2.2) * np.clip((dur - t) / .5, 0, 1)

# scene-aligned harmony (start time, bass, chord tones)
SEG = [(0.0, 38, [62, 66, 69, 73, 76]),
       (3.2, 38, [62, 66, 69, 73, 76]),
       (9.0, 35, [59, 62, 66, 69, 73]),
       (12.8, 43, [59, 62, 66, 67, 71]),
       (16.6, 40, [59, 62, 66, 67, 71]),
       (21.4, 45, [61, 64, 69, 71, 76]),
       (25.0, 42, [61, 64, 66, 69, 73]),
       (28.2, 43, [62, 66, 67, 69, 71]),
       (31.3, 45, [62, 64, 67, 69, 73]),
       (34.33, 38, [62, 66, 69, 73, 78])]
STEP = 60 / 72 / 2   # eighth notes at 72 BPM
PAT = [0, 2, 3, 4, 3, 2, 1, 3]  # arpeggio order over chord tones
for i, (t0, bass, ch) in enumerate(SEG):
    t1 = SEG[i + 1][0] if i + 1 < len(SEG) else DUR
    d = t1 - t0
    add(pad([bass + 12] + ch[:3], d + 1.2), t0, .16 if i else .22)
    if i == 0:
        add(piano(ch[4] + 12, .35, 3), 1.0, .5, .2); add(piano(ch[2] + 12, .3, 3), 2.2, .45, -.2)
        continue
    add(sub(bass - 12, min(d, 3)), t0, .35); add(piano(bass, .5, min(d, 3.5)), t0, .45, -.25)
    if i == len(SEG) - 1:   # final: rolled chord + high bell notes
        for j, m in enumerate(ch): add(piano(m, .55, 2.6), t0 + j * .07, .4, -.3 + .15 * j)
        for j, m in enumerate([ch[4] + 12, ch[3] + 12, ch[2] + 24]): add(piano(m, .35, 1.6), t0 + .9 + j * .45, .32, .3)
        continue
    k = 0; t = t0 + STEP
    while t < t1 - .1:
        m = ch[PAT[k % 8]] + (12 if k % 8 == 4 else 0)
        vel = .42 + .12 * (k % 4 == 0) + rng.uniform(-.04, .04)
        add(piano(m, vel, STEP * 3), t + rng.uniform(-.008, .008), .26, (m - 66) / 30)
        k += 1; t += STEP
    # melodic top line on longer sections
    if d > 4:
        for j, (dt, off) in enumerate([(0.0, 0), (STEP * 3, 2), (STEP * 6, 1)]):
            add(piano(ch[4] + 12 - [0, 3, 5][off], .5, 2.2), t0 + dt + STEP * 0.5, .22, .15)

# reverb: decaying filtered noise IR, stereo
def ir(seed):
    r = np.random.default_rng(seed); n = int(3.4 * SR); t = np.arange(n) / SR
    y = r.standard_normal(n) * np.exp(-t / .85)
    y = lowpass(y, 5200) * .6 + lowpass(y, 1400) * .4
    y[:int(.012 * SR)] = 0
    return y / np.sqrt(np.sum(y ** 2))
def conv(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[:len(x)]
wetL, wetR = conv(L, ir(1)), conv(R, ir(2))
outL, outR = L * .78 + wetL * .55, R * .78 + wetR * .55
fade = int(2.2 * SR)
for o in (outL, outR):
    o[:int(.3 * SR)] *= np.linspace(0, 1, int(.3 * SR)); o[-fade:] *= np.linspace(1, 0, fade) ** 2
pk = max(np.abs(outL).max(), np.abs(outR).max()); outL /= pk / .9; outR /= pk / .9
os.makedirs('out', exist_ok=True)
with wave.open('out/music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([outL, outR], 1) * 32767).astype('<i2').tobytes())
print('ok')
