"""Original afro-pop groove, 117 BPM, drop on the 'after' reveal at 8.0 s -> out/afro.wav"""
import numpy as np, wave
SR, DUR, BPM, DROP = 44100, 18.0, 117, 8.0
B = 60 / BPM; S = B / 4; N = int(DUR * SR); mix = np.zeros(N); rng = np.random.default_rng(5)
def add(sig, t, g=1.0):
    i = int(round(t * SR))
    if 0 <= i < N: s = sig[:N - i]; mix[i:i + len(s)] += s * g
def env(n, a=.002, d=.2): t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)
def noise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
def kick():
    n = int(.4 * SR); t = np.arange(n) / SR; f = 48 + 130 * np.exp(-t / .025)
    return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .16))
def logdrum(m):  # pitched, gliding bass hit
    n = int(.5 * SR); t = np.arange(n) / SR; f = midi(m) * (1 + .5 * np.exp(-t / .02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(1.6 * (np.sin(ph) + .3 * np.sin(2 * ph))) * env(n, .003, .18)
def shaker(): n = int(.07 * SR); return noise(n, 6000, 15000) * env(n, .004, .018)
def clap():
    n = int(.25 * SR); e = env(n, .001, .07)
    for k in (.010, .021): e[int(k * SR):] += env(n - int(k * SR), .001, .05) * .6
    return noise(n, 1000, 6000) * e
def rim(): n = int(.06 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * 1700 * t) + noise(n, 2500, 7000) * .5) * env(n, .0005, .012)
def conga(f): n = int(.18 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * f * (1 + .15 * np.exp(-t / .01)) * t) * env(n, .001, .06)
def pluck(f, d=.25):
    n = int(.6 * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 * np.exp(-t * k * 3) for k in range(1, 7)); return y * env(n, .002, d)
def pad(fs, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * .3 * t)) + .3 * np.sin(4 * np.pi * f * t) for f in fs)
    e = np.minimum(t / .4, 1) * np.minimum((dur - t) / .4, 1); return y * e
def riser(d): n = int(d * SR); t = np.arange(n) / n; return (np.sin(2 * np.pi * np.cumsum(220 * 2 ** (t * 3)) / SR) * .3 + noise(n, 2000, 12000) * .7) * t ** 2.2
def whoosh(d=.4): n = int(d * SR); return noise(n, 1500, 9000) * (np.arange(n) / n) ** 3
# original progression in F# minor: F#m - D - A - E (one bar each)
PROG = [(42, [61, 66, 69]), (38, [62, 66, 69]), (45, [61, 64, 69]), (40, [59, 64, 68])]
BASS = [(0, 0), (3, 0), (6, 7), (10, 0), (12, 12), (14, 7)]           # 16th step, interval
KICK = [0, 6, 8, 11]                                                 # syncopated afro kick
CONG = [(2, 330), (5, 260), (7, 330), (9, 260), (13, 330), (15, 400)]
ARP = [0, 3, 6, 8, 10, 13]
first = DROP - int(DROP / B) * B                                    # grid phase: downbeat lands on DROP
bar0 = -int(DROP / B) // 4 * 1
t = first; step = 0
beat_idx = lambda tt: round((tt - DROP) / B)
s = first - 16 * S * 4
while s < DUR:
    s += S
    if s < 0: continue
    k = round((s - DROP) / S); st = k % 16; bar = (k // 16) % 4
    root, tri = PROG[bar]
    pre = s < DROP; end = s >= 15.3
    if s >= 1.7 or True:
        add(shaker(), s, (.10 if st % 2 else .16) * (.6 if pre else 1))
    if pre:
        if st in (0, 8): add(kick(), s, .55)
        if st in (4, 12): add(rim(), s, .25)
        if st in ARP: add(pluck(midi(tri[ARP.index(st) % 3] + 12)), s, .10)
    else:
        if st in KICK: add(kick(), s, .9 if st == 0 else .65)
        if st in (4, 12): add(clap(), s, .38)
        for bs, iv in BASS:
            if st == bs: add(logdrum(root - 12 + iv), s, .42)
        for cs, f in CONG:
            if st == cs: add(conga(f), s, .2)
        if st in ARP: add(pluck(midi(tri[ARP.index(st) % 3] + 24), .18), s, .09)
    if st == 0: add(pad([midi(m) for m in tri], 16 * S + .3), s, .018 if pre else .026)
add(riser(4 * B), DROP - 4 * B, .3)
for i in range(8): add(clap(), DROP - B + i * B / 8, .06 + .03 * i)
add(kick(), DROP, 1.1); n = int(1.6 * SR); add(noise(n, 300, 8000) * env(n, .002, .45), DROP, .32)
for t in (1.6, 7.0, 12.8, 14.75): add(whoosh(), t - .4, .22)
add(kick(), 15.3, 1.0); n = int(1.2 * SR); add(noise(n, 300, 6000) * env(n, .002, .35), 15.3, .25)
mix[:int(.15 * SR)] *= np.linspace(0, 1, int(.15 * SR))
fade = int(1.3 * SR); mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
mix = np.tanh(mix * 1.15); mix = mix / np.abs(mix).max() * .89
with wave.open('out/afro.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype('<i2').tobytes())
print('ok', round(B, 4))
