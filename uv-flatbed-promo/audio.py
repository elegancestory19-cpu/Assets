"""Synthesize the music + SFX bed (124 BPM, 50 beats) -> out/music.wav"""
import numpy as np, wave, os
SR, BPM, BEATS = 44100, 124, 50
B = 60 / BPM
N = int(round(BEATS * B * SR))
mix = np.zeros(N)
rng = np.random.default_rng(7)

def add(sig, t, g=1.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i]
    mix[i:i + len(s)] += s * g

def env(n, a=0.003, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)

def kick():
    n = int(.32 * SR); t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .11)

def bandnoise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)

def hat(d=.03):
    n = int(.12 * SR); return bandnoise(n, 7000, 16000) * env(n, .001, d)

def clap():
    n = int(.22 * SR); e = env(n, .001, .07)
    for k in (.011, .023): e[int(k * SR):] += env(n - int(k * SR), .001, .05) * .7
    return bandnoise(n, 900, 5000) * e

def tone(freq, dur, kind='saw', d=.25):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == 'saw':
        y = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 9))
    elif kind == 'sq':
        y = sum(np.sin(2 * np.pi * freq * k * t) / k for k in (1, 3, 5))
    else:
        y = np.sin(2 * np.pi * freq * t)
    return y * env(n, .004, d)

def whoosh(dur=.5):
    n = int(dur * SR); t = np.arange(n) / n
    return bandnoise(n, 1500, 9000) * t ** 3 * np.exp(-((t - 1) * 0) )

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / n
    f = 200 * 2 ** (t * 3)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .35 + bandnoise(n, 2000, 12000) * .6) * t ** 2

midi = lambda m: 440 * 2 ** ((m - 69) / 12)
# A minor: Am F C G, one chord per 4 beats
CH = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
K, H, C = kick(), hat(), clap()

add(K, 0, 1.0); add(tone(55, 1.6, 'sin', .7), 0, .6)
add(riser(4 * B - .05), .05, .22)
for b in range(4, 40):
    root, tri = CH[(b // 4) % 4]
    t = b * B
    add(K, t, .95)
    add(H, t + B / 2, .22)
    if b >= 12:
        add(H, t + B / 4, .1); add(H, t + 3 * B / 4, .1)
        if b % 2 == 1: add(C, t, .32)
    # bass: off-beat pump
    add(tone(midi(root - 12), B * .45, 'sq', .16), t + B / 2, .34)
    if b >= 20: add(tone(midi(root - 12), B * .2, 'sq', .08), t + 3 * B / 4, .22)
    # pluck arp (8ths, 16ths from the print section)
    steps = 4 if b >= 12 else 2
    for s in range(steps):
        note = tri[(b * steps + s) % 3] + (12 if (s % 2 and b >= 20) else 0)
        add(tone(midi(note), .22, 'saw', .07), t + s * B / steps, .085 if b >= 12 else .07)
    if b % 4 == 0:  # pad
        for m in tri: add(tone(midi(m), 4 * B, 'sin', 2.2), t, .05)
# whooshes into every picture cut
for b in (4, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40):
    add(whoosh(.42), b * B - .42, .2)
add(riser(2 * B), 38 * B, .2)
# end card: impact + held chord + soft pulse
add(K, 40 * B, 1.1); add(tone(55, 2.5, 'sin', 1.1), 40 * B, .7); add(bandnoise(int(1.2 * SR), 300, 6000) * env(int(1.2 * SR), .002, .35), 40 * B, .3)
for m in (57, 60, 64, 69): add(tone(midi(m), 10 * B, 'saw', 2.6), 40 * B, .035); add(tone(midi(m), 10 * B, 'sin', 3.0), 40 * B, .06)
for b in range(42, 49, 2): add(K, b * B, .6); add(H, b * B + B / 2, .12)
for i, m in enumerate((69, 72, 76, 81)): add(tone(midi(m), .6, 'saw', .18), 44 * B + i * B / 2, .07)

fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
mix = np.tanh(mix * 1.15)
mix = mix / np.abs(mix).max() * .89
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'music.wav')
pcm = (np.stack([mix, mix], 1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(out, N / SR)
