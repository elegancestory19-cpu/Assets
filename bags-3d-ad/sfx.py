"""Soft sound design driven by the same event list: glass taps on card snaps, airy whooshes on camera moves,
a gentle low pad. Low-passed, no percussion. -> out/sfx.wav"""
import numpy as np, wave
SR, DUR = 44100, 23.6
WARP=[[0,0],[2.95,2.4],[7.9,5.5],[8.3,5.7],[12.4,9.25],[12.96,10.3],[13.47,11.4],[14.6,12.5],[15.7,13.4],[17.7,17.3],[18.3,17.6],[21.1,20.0],[23.6,22.5]]
def inv(a):
    for (o1,a1),(o2,a2) in zip(WARP,WARP[1:]):
        if a<=a2: return o1+(o2-o1)*(a-a1)/(a2-a1)
    return DUR
N = int(DUR * SR); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(4)
def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / (1 + (f / fc) ** 4), len(x))
def add(s, t, g=1, pan=0):
    i = int(t * SR); s = s[:max(0, N - i)] * g
    L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2); R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2)
def tap(f=1320):  # soft glass tap / chime
    n = int(1.2 * SR); t = np.arange(n) / SR
    y = np.sin(2*np.pi*f*t) * np.exp(-t/.35) + .4*np.sin(2*np.pi*f*2.01*t) * np.exp(-t/.18) + .2*np.sin(2*np.pi*f*.5*t)*np.exp(-t/.5)
    return lp(y * np.minimum(t / .004, 1), 3500)
def whoosh(d=.7):
    n = int(d * SR); t = np.arange(n) / n; y = rng.standard_normal(n)
    return lp(y, 1400) * np.sin(np.pi * t) ** 2
def click(): n = int(.06*SR); t=np.arange(n)/SR; return lp(rng.standard_normal(n)*np.exp(-t/.008),2500)
def pad(ms, d):
    n = int(d*SR); t=np.arange(n)/SR; y=sum(np.sin(2*np.pi*440*2**((m-69)/12)*t + rng.uniform(0,6)) for m in ms)
    return lp(y*np.clip(t/2,0,1)*np.clip((d-t)/2,0,1),700)/len(ms)
CARDS = [.55, 4.2, 6.05, 6.8, 7.6, 9.3, 13.5, 14.3, 16.0, 18.7]
for i, t in enumerate(CARDS): add(tap([1320, 1480, 1568, 1760][i % 4]), inv(t) + .1, .16, (-1) ** i * .3)
for t in [10.3, 11.4, 12.5]: add(click(), inv(t), .35); add(tap(1976), inv(t) + .02, .12)
for t in [1.0, 5.6, 6.6, 7.5, 8.5, 13.3, 15.4, 17.2]: add(whoosh(.8), inv(t) - .4, .22)
add(whoosh(1.2), inv(2.4), .12)                      # print scan
add(tap(880), inv(18.0), .25); add(tap(1320), inv(18.0)+.05, .15)   # logo lock-up
add(pad([50, 57, 62, 66], 12.5), 0, .16); add(pad([47, 54, 59, 62], 12.6), 11.0, .16)
for o in (L, R):
    o[-int(1.5*SR):] *= np.linspace(1, 0, int(1.5*SR)) ** 2
pk = max(np.abs(L).max(), np.abs(R).max()); L /= pk / .8; R /= pk / .8
with wave.open('out/sfx.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L,R],1)*32767).astype('<i2').tobytes())
print('ok')
