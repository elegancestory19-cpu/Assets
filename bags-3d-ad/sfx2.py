"""Cinematic sound design for the 3D bags ad, driven by the same event list as the picture.
Every sound is shaped like a real object: filtered-noise whooshes with a moving centre frequency and
stereo pan, glass clinks with inharmonic partials, mechanical drum ticks, sub impacts on landings,
a reverse swell into the logo, all sent through one shared stereo room. -> out/sfx2.wav"""
import numpy as np, wave
SR, DUR = 44100, 23.6
WARP = [[0,0],[2.95,2.4],[7.9,5.5],[8.3,5.7],[12.4,9.25],[12.96,10.3],[13.47,11.4],[14.6,12.5],[15.7,13.4],[17.7,17.3],[18.3,17.6],[21.1,20.0],[23.6,22.5]]
def inv(a):  # animation time -> output time
    for (o1, a1), (o2, a2) in zip(WARP, WARP[1:]):
        if a <= a2: return o1 + (o2 - o1) * (a - a1) / (a2 - a1)
    return DUR
N = int(DUR * SR)
dry = np.zeros((N, 2)); send = np.zeros((N, 2))
rng = np.random.default_rng(11)

def place(sig, t, g=1.0, pan=0.0, rev=.25):
    """sig: mono or (n,2). pan -1..1 constant-power. rev = send to the room."""
    i = int(t * SR)
    if i >= N: return
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4; sig = np.stack([sig * np.cos(a), sig * np.sin(a)], 1)
    s = sig[:N - i] * g
    dry[i:i + len(s)] += s; send[i:i + len(s)] += s * rev

def svf_bp(x, fc, q):
    """time-varying band-pass (state-variable filter); fc may be an array."""
    fc = np.broadcast_to(fc, x.shape)
    y = np.zeros_like(x); lp = bp = 0.0
    f = 2 * np.sin(np.pi * np.clip(fc, 20, 16000) / SR); d = 1 / q
    for n in range(len(x)):
        hp = x[n] - lp - d * bp; bp += f[n] * hp; lp += f[n] * bp; y[n] = bp
    return y

def lowpass(x, fc):
    X = np.fft.rfft(x, axis=0); fr = np.fft.rfftfreq(len(x), 1 / SR)
    h = 1 / np.sqrt(1 + (fr / fc) ** 8)
    return np.fft.irfft(X * (h[:, None] if X.ndim == 2 else h), len(x), axis=0)

def whoosh(d=.9, f0=300, f1=2400, pan0=-.8, pan1=.8, body=1.0):
    """air passing the lens: band-passed noise whose centre sweeps and whose pan travels."""
    n = int(d * SR); t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t ** .8) ** 2.2
    fc = f0 * (f1 / f0) ** (np.sin(np.pi * t / 2) ** 1.5) * (1 - .35 * t ** 4)
    y = svf_bp(rng.standard_normal(n), fc, 1.6) * env
    y += body * svf_bp(rng.standard_normal(n), fc * .35, 2.5) * env * .6   # low body
    y /= np.abs(y).max() + 1e-9
    p = pan0 + (pan1 - pan0) * t; a = (p + 1) * np.pi / 4
    return np.stack([y * np.cos(a), y * np.sin(a)], 1)

def clink(f=2200, d=1.4):
    """glass card settling: inharmonic partials + tiny contact click."""
    n = int(d * SR); t = np.arange(n) / SR
    parts = [(1.0, 1.0, .9), (2.76, .55, .45), (5.40, .3, .22), (8.93, .16, .12)]
    y = sum(a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6)) * np.exp(-t / tau) for r, a, tau in parts)
    y *= np.minimum(t / .0015, 1)
    k = int(.004 * SR); y[:k] += rng.standard_normal(k) * np.linspace(1, 0, k) * .5
    return y * .5

def thock(f=110):
    """soft UI press: felt-like low thump + short filtered tick."""
    n = int(.25 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t * (1 + .6 * np.exp(-t / .01))) * np.exp(-t / .045)
    k = int(.012 * SR); y[:k] += lowpass(rng.standard_normal(k), 3500) * np.exp(-np.arange(k) / (.002 * SR)) * .9
    return y

def tick():
    """mechanical drum detent."""
    n = int(.05 * SR); t = np.arange(n) / SR
    y = svf_bp(rng.standard_normal(n), 3200, 6) * np.exp(-t / .006) + .4 * np.sin(2 * np.pi * 900 * t) * np.exp(-t / .01)
    return y

def impact(f0=70, d=1.6, bright=.35):
    """bag landing: pitch-dropping sub + short broadband thud."""
    n = int(d * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-t / .03))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .35)
    k = int(.08 * SR); y[:k] += lowpass(rng.standard_normal(k), 900) * np.exp(-np.arange(k) / (.012 * SR)) * bright
    return np.tanh(1.4 * y)

def reverse_swell(d=1.2):
    n = int(d * SR); t = np.linspace(0, 1, n)
    y = svf_bp(rng.standard_normal(n), 600 + 5000 * t ** 2, 1.2) * t ** 3
    return y / (np.abs(y).max() + 1e-9)

def scan(d=2.2):
    """print head travelling: filtered noise with a soft motor hum, panned slowly."""
    n = int(d * SR); t = np.linspace(0, 1, n); s = np.arange(n) / SR
    env = np.minimum(t / .08, 1) * np.minimum((1 - t) / .1, 1)
    y = svf_bp(rng.standard_normal(n), 1800 + 600 * np.sin(2 * np.pi * 3 * t), 3) * .5
    y += .35 * np.sin(2 * np.pi * 180 * s) * (1 + .3 * np.sin(2 * np.pi * 24 * s))
    y *= env
    p = -.4 + .8 * t; a = (p + 1) * np.pi / 4
    return np.stack([y * np.cos(a), y * np.sin(a)], 1)

def room_tone(d):
    n = int(d * SR)
    y = lowpass(rng.standard_normal((n, 2)), 500) * .02
    return y

# ---------------- event list (animation seconds, mapped to output with inv) ----------------
place(room_tone(DUR), 0, 1.0, rev=0)
place(whoosh(1.3, 200, 1400, -.3, .3, 1.3), 0.0, .55)                       # bag spins in
CARDS = [(.55, 2100, -.2), (4.2, 2350, .25), (6.05, 1900, -.5), (6.8, 2100, 0), (7.6, 2350, .5),
         (9.3, 1980, 0), (13.5, 2200, -.3), (14.3, 2400, .3), (16.0, 2050, 0), (18.7, 2250, 0)]
for t, f, p in CARDS:
    place(whoosh(.35, 900, 3500, p - .4, p, .3), inv(t) - .12, .18)          # card swings open
    place(clink(f), inv(t) + .28, .32, p, rev=.45)                           # glass settles
place(scan(inv(4.25) - inv(2.6)), inv(2.6), .35, rev=.2)                     # print pass
place(clink(3100, .8), inv(4.2), .18, 0, rev=.5)                            # print done sparkle
for t, p in [(5.3, -.6), (5.6, .6)]:                                          # bags rise and land
    place(whoosh(.7, 120, 700, p, p, 1.4), inv(t) - .1, .35)
    place(impact(64 if p < 0 else 52), inv(t + .75), .55, p * .5, rev=.3)
for t0, t1, p0, p1 in [(5.8, 6.4, .3, -.6), (6.6, 7.2, -.6, .2), (7.4, 8.0, .2, .7), (8.3, 9.1, .7, -.6),
                       (13.0, 13.7, -.4, .4), (13.9, 14.7, -.2, .7), (15.2, 16.1, .5, -.5), (17.0, 17.6, -.3, .3)]:
    d = max(.45, inv(t1) - inv(t0))
    place(whoosh(d, 250, 2200, p0, p1), inv(t0), .42)                        # camera moves
for t in [10.3, 11.4, 12.5]:
    place(thock(), inv(t), .6, 0, rev=.2)                                     # pill press
for t in [11.4, 12.5]:                                                         # drums roll: detents
    for k in range(4): place(tick(), inv(t) + .05 + k * .07, .22 - k * .03, (-.3, .3)[k % 2], rev=.15)
R = np.random.default_rng(3)                                                   # crowd rising: cascade
for k in range(26):
    t = 15.0 + k * .07 + R.uniform(0, .05)
    place(impact(55 + R.uniform(-8, 8), .6, .5), inv(t) + .25, .1 + .1 * R.random(), R.uniform(-.9, .9), rev=.35)
place(reverse_swell(1.1), inv(17.7) - .6, .38, rev=.3)                       # into the logo
place(impact(44, 2.4, .6), inv(17.75) + .45, .85, 0, rev=.5)                 # logo lands
place(clink(1650, 2.4), inv(17.75) + .5, .3, 0, rev=.6)
place(whoosh(.6, 400, 3000, -.5, .5), inv(20.0) - .3, .35)                    # end card
place(clink(2640, 2.0), inv(20.0) + .05, .25, 0, rev=.6)

# ---------------- shared stereo room ----------------
def ir(seed, d=2.2):
    r = np.random.default_rng(seed); n = int(d * SR); t = np.arange(n) / SR
    y = r.standard_normal(n) * np.exp(-t / .55); y[:int(.015 * SR)] = 0
    y = lowpass(y, 5000); return y / np.sqrt((y ** 2).sum())
def conv(x, h):
    m = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:len(x)]
wet = np.stack([conv(send[:, 0], ir(1)), conv(send[:, 1], ir(2))], 1)
mix = dry + wet * .9
mix -= lowpass(mix, 35)                       # rumble cut
mix = np.tanh(mix * 1.2) / np.tanh(1.2)       # gentle glue
mix[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))[:, None] ** 2
mix /= np.abs(mix).max() / .85
with wave.open('out/sfx2.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', round(DUR, 2))
