"""Cinematic sound design for the 3D bags ad, driven by the same event list as the picture.
Every sound is shaped like a real object: filtered-noise whooshes with a moving centre frequency and
stereo pan, glass clinks with inharmonic partials, mechanical drum ticks, sub impacts on landings,
a reverse swell into the logo, all sent through one shared stereo room. -> out/sfx2.wav"""
import numpy as np, wave
SR, DUR = 44100, 29.0
WARP = [[0,0],[7.7,1.0],[10.0,2.0],[11.7,4.9],[14.0,8.6],[18.35,11.4],[23.3,15.6],[24.6,18.6],[26.3,20.8],[29.0,23.3]]
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

# ---------------- event list (Lights On) ----------------
_place=place
def place(sig,t,g=1.0,pan=0.0,rev=.25): _place(sig,inv(t) if t>0 else 0,g,pan,rev)
import json
PAIRS = json.load(open('out/pairs.json'))
_place(room_tone(DUR), 0, 1.0, rev=0)
def pad(ms, d):
    n=int(d*SR); t=np.arange(n)/SR; y=sum(np.sin(2*np.pi*440*2**((m-69)/12)*t+rng.uniform(0,6)) for m in ms)
    return lowpass(y*np.clip(t/1.5,0,1)*np.clip((d-t)/1.5,0,1),650)/len(ms)
_place(pad([45,52,57,61],12.0), 0, .2, rev=.3)                                 # night air
place(thock(150), 1.0, .7, .2, rev=.25); place(clink(2600,1.0), 1.0, .22, .2, rev=.5)   # the tap
place(whoosh(1.0, 1800, 300, .2, 0, .4), 1.02, .5)                           # bolt flies into depth
for k in range(3): place(tick(), 2.0+k/30, .5, (-.2,0,.2)[k], rev=.3)        # windows switch on, 3 frames
place(impact(80,1.2,.5), 2.0, .45, 0, rev=.4)
for j in range(8): place(clink(1400+j*90, .9), 2.18+j*.09, .09, (j%2-.5)*.6, rev=.5)   # glass blocks push out
place(whoosh(1.2, 200, 1600, -.5, .6, 1.2), 3.7, .45)                        # take-off over the city
for i,t in enumerate(PAIRS):
    place(tick(), t, .28, (-.6 if i%2 else .6), rev=.35)                   # window A
    place(clink(1700+(i%5)*120, .7), t+.9, .1, (.6 if i%2 else -.6), rev=.5)  # window B answers
for t0,t1,p0,p1 in [(4.6,5.6,-.5,.5),(5.8,6.5,.5,-.5),(8.4,9.2,-.3,.3)]:
    place(whoosh(t1-t0, 250, 2000, p0, p1), t0, .38)
spin=whoosh(.9, 300, 3000, -1, 1, 1.0); place(spin, 6.5, .5); place(whoosh(.7, 3000, 400, 1, -1, .6), 7.0, .35)   # barrel roll
place(reverse_swell(1.4), 8.6, .45, rev=.4)                                   # panes peel off
R2=np.random.default_rng(8)
for k in range(30): place(clink(1500+R2.uniform(0,1600), .6), 9.0+k*.035+R2.uniform(0,.03), .05, R2.uniform(-.9,.9), rev=.5)
place(impact(42, 2.6, .7), 10.0, 1.0, 0, rev=.55); place(clink(1320, 2.2), 10.02, .3, 0, rev=.7)   # DROP: plates lock
place(whoosh(.6, 400, 2600, .6, -.4), 11.2, .4)                              # into the footage
place(svf_bp(rng.standard_normal(int(4.6*SR)), 900, 1.4)*.25*np.minimum(np.arange(int(4.6*SR))/SR/.3,1), 11.5, .35, rev=.15)  # print room air
place(whoosh(.6, 400, 2600, -.5, .5), 15.3, .4)
for i in range(5): place(clink([1980,2220,2350,2640,2960][i], 1.2), 15.95+i*.18, .2, (-.5,0,.5,-.25,.25)[i], rev=.5)
place(whoosh(.9, 300, 2600, -.6, .6), 18.45, .4)
for k in range(14): place(tick(), 18.7+k*.05, .12, ((k%2)-.5), rev=.4)
place(reverse_swell(.8), 18.6, .35, rev=.3); place(impact(46, 2.2, .6), 19.4, .85, 0, rev=.5); place(clink(1650, 2.2), 19.42, .3, 0, rev=.6)
place(whoosh(.5, 500, 3000, -.4, .4), 20.6, .3); place(clink(2640, 1.8), 20.85, .22, 0, rev=.6)

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
with wave.open('out/sfx.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', round(DUR, 2))
