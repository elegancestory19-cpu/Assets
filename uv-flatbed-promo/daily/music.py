"""Synthesize one music bed per episode from build.json -> out/music/epNN.wav"""
import numpy as np, wave, os, json, sys
SR = 44100
H = os.path.dirname(os.path.abspath(__file__))
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
PROG = [  # (bass root, triad) per bar; all minor-key, emotive
    [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])],   # Am F C G
    [(38, [57, 62, 65]), (46, [58, 62, 65]), (41, [57, 60, 65]), (48, [55, 60, 64])],   # Dm Bb F C
    [(40, [59, 64, 67]), (48, [60, 64, 67]), (43, [59, 62, 67]), (38, [57, 62, 66])],   # Em C G D
    [(48, [60, 63, 67]), (44, [60, 63, 68]), (39, [58, 63, 67]), (46, [58, 62, 65])],   # Cm Ab Eb Bb
    [(42, [61, 66, 69]), (38, [62, 66, 69]), (45, [61, 64, 69]), (40, [59, 64, 68])],   # F#m D A E
]
def make(e):
    rng = np.random.default_rng(100 + e['ep'])
    B = 60 / e['bpm']; nb, ne = e['beats'], e['endBeats']
    FD = e['nFoot'] / 30
    N = int(round((FD + ne * B) * SR)); mix = np.zeros(N)
    def add(sig, t, g=1.0):
        i = int(t * SR)
        if i >= N or i < 0: return
        s = sig[:N - i]; mix[i:i + len(s)] += s * g
    def env(n, a=.003, d=.2):
        t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)
    def noise(n, lo, hi):
        X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR); X[(f < lo) | (f > hi)] = 0
        y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)
    def kick(deep=False):
        n = int(.45 * SR); t = np.arange(n) / SR; f = (42 if deep else 48) + 110 * np.exp(-t / .03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (.2 if deep else .11))
    def hat(): n = int(.1 * SR); return noise(n, 7000, 16000) * env(n, .001, .03)
    def clap():
        n = int(.25 * SR); return noise(n, 900, 5000) * env(n, .001, .08)
    def tone(f, dur, kind, d):
        n = int(dur * SR); t = np.arange(n) / SR
        hs = {'saw': [(k, 1 / k) for k in range(1, 9)], 'sq': [(1, 1), (3, .33), (5, .2)], 'sin': [(1, 1)],
              'piano': [(1, 1), (2, .5), (3, .28), (4, .14), (5, .08), (6, .05)]}[kind]
        y = sum(a * np.sin(2 * np.pi * f * k * t) * (np.exp(-t * k * 1.2) if kind == 'piano' else 1) for k, a in hs)
        return y * env(n, .004, d)
    def riser(dur):
        n = int(dur * SR); t = np.arange(n) / n
        return (np.sin(2 * np.pi * np.cumsum(200 * 2 ** (t * 3)) / SR) * .3 + noise(n, 2000, 12000) * .6) * t ** 2
    prog = PROG[e['ep'] % len(PROG)]; tr = [0, -2, 3, -4, 2][e['ep'] % 5]
    drive = e['style'] == 'drive'
    K, Hh, C = kick(not drive), hat(), clap()
    motif = rng.permutation([0, 1, 2, 1, 2, 0, 2, 1])
    add(kick(True), 0, .9); add(riser(2 * B), 0, .12)
    for b in range(nb):
        root, tri = prog[(b // 4) % 4]; root += tr; tri = [m + tr for m in tri]; t = b * B
        full = b >= 2
        if b % 4 == 0:
            for m in tri: add(tone(midi(m), 4 * B + .5, 'sin', 2.5), t, .06); add(tone(midi(m), 4 * B, 'saw', 2.0), t, .012)
            add(tone(midi(root), 4 * B, 'sin', 1.6), t, .22)
        if drive:
            if full: add(K, t, .9); add(Hh, t + B / 2, .2); add(tone(midi(root - 12), B * .45, 'sq', .16), t + B / 2, .3)
            if b >= nb // 2:
                add(Hh, t + B / 4, .09); add(Hh, t + 3 * B / 4, .09)
                if b % 2: add(C, t, .28)
            for s in range(2 if b < nb // 2 else 4):
                st = 2 if b < nb // 2 else 4
                add(tone(midi(tri[motif[(b * st + s) % 8]] + 12), .3, 'piano', .22), t + s * B / st, .11)
        else:
            if full and b % 2 == 0: add(K, t, .8)
            if b >= nb // 2 and b % 2 == 1: add(C, t, .16); add(Hh, t + B / 2, .1)
            for s in range(2):
                add(tone(midi(tri[motif[(b * 2 + s) % 8]] + 12), 1.2, 'piano', .7), t + s * B / 2, .16)
            if b % 2 == 0: add(tone(midi(tri[2] + 24), 1.6, 'piano', .9), t, .07)
    mid = round(nb * .5) * B
    add(noise(int(.4 * SR), 1500, 9000) * (np.arange(int(.4 * SR)) / int(.4 * SR)) ** 3, mid - .4, .16)
    add(riser(2 * B), FD - 2 * B, .22)
    for i in range(4): add(C, FD - B + i * B / 4, .1 + .05 * i)
    # end card: impact, held chord, rising figure
    root, tri = prog[0]; root += tr; tri = [m + tr for m in tri]
    add(kick(True), FD, 1.1); add(tone(midi(root - 12), 3, 'sin', 1.2), FD, .6)
    n = int(1.2 * SR); add(noise(n, 300, 6000) * env(n, .002, .35), FD, .28)
    for m in tri + [tri[0] + 12]: add(tone(midi(m), ne * B, 'sin', 3), FD, .07); add(tone(midi(m), ne * B, 'saw', 2.5), FD, .02)
    for i, m in enumerate([tri[0] + 12, tri[1] + 12, tri[2] + 12, tri[0] + 24]): add(tone(midi(m), 1.6, 'piano', .9), FD + (1 + i * .5) * B, .15)
    fade = int(min(1.2, ne * B * .4) * SR); mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix = np.tanh(mix * 1.1); mix = mix / np.abs(mix).max() * .89
    os.makedirs(f'{H}/out/music', exist_ok=True)
    with wave.open(f"{H}/out/music/ep{e['ep']:02d}.wav", 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.stack([mix, mix], 1) * 32767).astype('<i2').tobytes())
    return N / SR
only = set(map(int, sys.argv[1:]))
for e in json.load(open(f'{H}/build.json')):
    if not only or e['ep'] in only: print(e['ep'], e['style'], e['bpm'], round(make(e), 2))
