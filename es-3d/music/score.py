"""Event-driven score for «مدينة Elegance Story». Real recorded instruments only (VCSL, FreePats, Karoryfer: CC0). No SFX.
120 BPM, D major pentatonic. Every arrival in the picture (events.json) plays its own note: building is composing.
Run: LIB=<lib> $LIB/.venv/bin/python music/score.py   →  music/score.wav, music/CREDITS_music.txt
"""
import os, sys, json
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR
HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, '..', 'events.json'))); EVS, DUR = E['ev'], E['dur']
K = {e['name']: e['t'] for e in EVS if e['type'] == 'cue'}
N = int(round(DUR * SR)); S.seed(20261104); R = np.random.default_rng(7)
OUT = []
def ev(t, inst, p, d, v, pan=0.0, gain=1.0, **kw):
    e = dict(t=float(t), inst=inst, pitch=p, dur=d, vel=v, pan=pan, gain=gain); e.update(kw); OUT.append(e)
def fold(m, lo, hi):
    while m > hi: m -= 12
    while m < lo: m += 12
    return m

# ── picture events → notes (the melody is written by the building)
for e in EVS:
    t, n, ty = e['t'], e.get('note'), e['type']
    if n is None: continue
    pan = R.uniform(-.4, .4)
    if ty == 'tile':   ev(t, 'kalimba', fold(n, 62, 73), .6, .5, pan, .9)
    elif ty == 'pop':  ev(t, 'marimba', fold(n, 62, 86), .5, .55, pan)
    elif ty == 'drop': ev(t, 'marimba', fold(n - 12, 50, 69), .5, .6, pan); ev(t, 'jazz_bass', fold(n - 24, 38, 50), .4, .35, 0, .7)
    elif ty == 'motif': ev(t, 'glockenspiel', n, 2.5, .5, 0, .9, release=2.0)
    elif ty == 'press': ev(t, 'jazz_bass', 38, .8, .8, 0, 1.1); ev(t, 'marimba', 50, .6, .6)
    elif ty in ('banner', 'sign'): [ev(t + i * .06, 'vibraphone', p, 1.6, .45, (i - 1) * .3, .8) for i, p in enumerate([n, n + 4, n + 7])]
    elif ty == 'replay': ev(t, 'glockenspiel', fold(n + 12, 79, 98), 1.2, .32, pan, .65); ev(t, 'kalimba', fold(n, 62, 73), .6, .42, -pan, .8)
    elif ty == 'screen':
        for p in [62, 66, 69, 76]: ev(t, 'vibraphone', p, 2.5, .5, R.uniform(-.3, .3), .8)
        ev(t, 'glockenspiel', 86, 3.0, .55, 0, .9, release=2.5); ev(t, 'glockenspiel', 74, 3.0, .45, 0, .8, release=2.5)
        ev(t, 'jazz_bass', 38, 2.0, .75, 0, 1.1)

# ── a bowed-vibraphone drone through the day (D), dusk (Bm), night (D add9)
for t0, d, ch in [(0.0, 7.4, ['D4', 'A4']), (7.5, 6.0, ['D4', 'F#4', 'A4']), (13.5, 5.0, ['B3', 'D4', 'F#4']), (18.5, 5.7, ['G3', 'B3', 'D4'])]:
    for p in ch: ev(t0, 'vibraphone_bowed', p, d, .26, R.uniform(-.3, .3), .5, attack=.8, release=.6)
for p in ['D4', 'F#4', 'A4', 'E5']: ev(K['night'] + .02, 'vibraphone_bowed', p, DUR - K['night'] - .5, .28, R.uniform(-.3, .3), .5, attack=1.2, release=.8)

# ── a gentle marimba ostinato (quarter notes) from the design island to dusk
ost = ['D4', 'A4', 'F#4', 'A4']
for i, t in enumerate(np.arange(3.0, K['zero0'] - .01, .5)):
    ev(t, 'marimba', ost[i % 4], .35, .32 if t < 7.5 else .36, -.2 + .4 * (i % 2), .7)
# ── darbuka (light), from the first bridge until the silence: doum on 1, tak on the off-beats
for b, t in enumerate(np.arange(7.5, K['zero0'] - .01, 2.0)):
    ev(t, 'world_perc', 'darbuka_doom', None, .55, 0, .55)
    for o in [.5, 1.25, 1.5]:
        if t + o < K['zero0']: ev(t + o, 'world_perc', 'darbuka_tak', None, .42, .15, .45)
    if t + 1.0 < K['zero0']: ev(t + 1.0, 'world_perc', 'darbuka_doom', None, .45, 0, .45)
# ── the end: the motif once more, softly, then ring out
ev(K['end'] + .5, 'glockenspiel', 86, 3.0, .32, 0, .7, release=3.0)
ev(K['end'] + .5, 'jazz_bass', 38, 2.5, .55, 0, 1.0)

OUT.sort(key=lambda e: e['t'])
mix = S.render(OUT, dur=DUR, master=False)
mix = S.room(mix, size=.42, mix=.18)
z0, z1 = int(K['zero0'] * SR), int((K['night'] - .004) * SR)     # one beat of digital zero before the night
f = int(.006 * SR); mix[z0 - f:z0] *= np.linspace(1, 0, f)[:, None]; mix[z0:z1] = 0
f0 = int((DUR - 1.0) * SR); mix[f0:] *= np.linspace(1, 0, N - f0)[:, None] ** 2
mix = mix[:N] / max(1e-9, np.abs(mix).max()) * .89
sf.write(os.path.join(HERE, 'score.wav'), mix.astype(np.float32), SR)
used = sorted({e['inst'] for e in OUT})
open(os.path.join(HERE, 'CREDITS_music.txt'), 'w').write('Instruments: ' + ', '.join(used) + '\n' + '\n'.join(S.credits(used)) + '\n')
print('score.wav', DUR, 's,', len(OUT), 'notes,', used)
