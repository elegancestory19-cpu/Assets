"""Music + SFX for the 18 s before/after story -> out/music.wav"""
import numpy as np, wave, os
SR, DUR, BPM = 44100, 18.0, 100
B = 60 / BPM; N = int(DUR * SR); mix = np.zeros(N); rng = np.random.default_rng(11)
def add(sig, t, g=1.0):
    i = int(t * SR)
    if 0 <= i < N: s = sig[:N - i]; mix[i:i + len(s)] += s * g
def env(n, a=.003, d=.2): t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)
def noise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
def kick(deep=False):
    n = int(.5 * SR); t = np.arange(n) / SR; f = (40 if deep else 50) + 120 * np.exp(-t / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (.25 if deep else .11))
def tone(f, dur, kind, d):
    n = int(dur * SR); t = np.arange(n) / SR
    hs = {'saw': [(k, 1 / k) for k in range(1, 9)], 'sin': [(1, 1)], 'piano': [(1, 1), (2, .5), (3, .28), (4, .14), (5, .08)]}[kind]
    return sum(a * np.sin(2 * np.pi * f * k * t) * (np.exp(-t * k * 1.2) if kind == 'piano' else 1) for k, a in hs) * env(n, .004, d)
def whoosh(d=.45): n = int(d * SR); return noise(n, 1500, 9000) * (np.arange(n) / n) ** 3
def riser(d): n = int(d * SR); t = np.arange(n) / n; return (np.sin(2 * np.pi * np.cumsum(180 * 2 ** (t * 3)) / SR) * .3 + noise(n, 2000, 12000) * .6) * t ** 2
def click(): n = int(.03 * SR); return noise(n, 2000, 8000) * env(n, .0005, .006)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
H = noise(int(.1 * SR), 7000, 16000) * env(int(.1 * SR), .001, .03)
C = noise(int(.25 * SR), 900, 5000) * env(int(.25 * SR), .001, .08)
# hook
add(kick(True), 0, .9); add(tone(midi(45) / 2, 1.6, 'sin', .8), 0, .5); add(kick(True), .7, .6)
add(whoosh(), 1.2, .25)
# design phase: soft piano arp + pulse, 1.7 - 7.6
t0 = 1.7; b = 0
while t0 + b * B < 7.5:
    t = t0 + b * B; root, tri = CH[(b // 4) % 4]
    if b % 4 == 0:
        for m in tri: add(tone(midi(m), 4 * B, 'sin', 2.2), t, .05)
        add(tone(midi(root - 12), 4 * B, 'sin', 1.5), t, .2)
    add(kick(), t, .45 if b % 2 == 0 else .25); add(H, t + B / 2, .12)
    for s in range(2): add(tone(midi(tri[(b * 2 + s) % 3] + 12), 1.0, 'piano', .6), t + s * B / 2, .13)
    b += 1
for t in (3.25, 3.33, 4.12, 4.2): add(click(), t, .35)        # cursor clicks
for t in (2.55, 2.9): add(noise(int(1.0 * SR), 3000, 10000) * np.hanning(int(1.0 * SR)), t, .06)  # scan
add(riser(1.4), 6.6, .3); add(whoosh(.5), 7.05, .3)
# reveal impact 8.0 and driving beat to 14.8
add(kick(True), 8.0, 1.2); add(tone(midi(33), 2.5, 'sin', 1.2), 8.0, .7)
n = int(1.4 * SR); add(noise(n, 300, 7000) * env(n, .002, .4), 8.0, .35)
for m in (57, 60, 64, 69): add(tone(midi(m), 3, 'saw', 1.8), 8.0, .03)
b = 0; B2 = 60 / 120
while 8.0 + b * B2 < 14.7:
    t = 8.0 + b * B2; root, tri = CH[(b // 4) % 4]
    if b: add(kick(), t, .8)
    add(H, t + B2 / 2, .18); add(H, t + B2 / 4, .07); add(H, t + 3 * B2 / 4, .07)
    if b % 2: add(C, t, .25)
    add(tone(midi(root - 12), B2 * .45, 'saw', .14), t + B2 / 2, .16)
    for s in range(2): add(tone(midi(tri[(b * 2 + s) % 3] + 12), .4, 'piano', .25), t + s * B2 / 2, .1)
    b += 1
add(whoosh(.5), 12.3, .25); add(riser(1.0), 13.8, .22); add(whoosh(.4), 14.75, .3)
# end card
add(kick(True), 15.3, 1.0); add(tone(midi(33), 2.5, 'sin', 1.1), 15.3, .6)
for m in (57, 60, 64, 69): add(tone(midi(m), 2.7, 'sin', 2.5), 15.3, .07)
for i, m in enumerate((69, 72, 76, 81)): add(tone(midi(m), 1.4, 'piano', .8), 15.8 + i * .25, .14)
fade = int(1.0 * SR); mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
mix = np.tanh(mix * 1.1); mix = mix / np.abs(mix).max() * .89
os.makedirs('out', exist_ok=True)
with wave.open('out/music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype('<i2').tobytes())
print('ok')
