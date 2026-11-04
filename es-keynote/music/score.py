"""Original score for «كلّش تحت سقف واحد» (Elegance Story). Real recorded instruments only (VCSL + Karoryfer, CC0).
120 BPM, A Dorian → A major at the snap. Reads ../timeline.json. Writes score.wav + CREDITS_music.txt.
Run: $LIB/.venv/bin/python music/score.py   (LIB on sys.path via env LIB)
"""
import os, sys, json
import numpy as np
import soundfile as sf
LIB = os.environ.get('LIB', '/root/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, '..', 'timeline.json')))
K, DUR = TL['K'], TL['DUR']
N = int(round(DUR * SR))
S.seed(20261104); R = np.random.default_rng(19)
EV = []          # (t, inst, pitch, dur, vel, pan, gain)
def ev(t, inst, p, d, v, pan=0.0, gain=1.0, **kw):
    e = dict(t=float(t), inst=inst, pitch=p, dur=d, vel=v, pan=pan, gain=gain); e.update(kw); EV.append(e)

DOR = [57, 59, 60, 62, 64, 66, 67, 69, 71, 72, 74, 76, 78, 79, 81]   # A Dorian (A B C D E F# G)

# S1 storm: one scattered note per card, detuned ±30 c, random pans, a different timbre per source
for i, t in enumerate(TL['STORM']):
    inst = ['marimba', 'vibraphone_hard', 'xylophone'][i % 3]
    m = DOR[R.integers(0, len(DOR))] + R.uniform(-0.3, 0.3) + (12 if inst == 'xylophone' else 0)
    ev(t, inst, m, 0.35, 0.35 + 0.3 * (t / 4.0), pan=R.uniform(-0.9, 0.9), gain=0.8)

# S3 the click: the first sound after the silence
ev(K['click'], 'glockenspiel', 'A6', 2.5, 0.55, gain=0.9, release=2.0)
ev(K['click'], 'marimba', 'A2', 1.5, 0.7)
for p in ['A3', 'C4', 'E4', 'G4', 'B4']:
    ev(K['click'] + 0.02, 'vibraphone_bowed', p, 4.3, 0.42, pan=R.uniform(-0.3, 0.3), attack=0.5, release=0.8, gain=0.7)

# S4–S9 additive marimba process: 8-eighth pattern, one more note each bar from 10.0
PAT = ['A4', 'E5', 'D5', 'B4', 'C5', 'E5', 'G4', 'A4']
def pattern_bar(t0, n, vel=0.5, inst='marimba', oct_=0, gain=1.0):
    for k in range(n):
        p = S.midi(PAT[k]) + 12 * oct_
        ev(t0 + k * 0.25, inst, p, 0.4, vel * (1.08 if k == 0 else 1.0), pan=(-0.25 + 0.5 * (k / 7)), gain=gain)
bar = 0
for t0 in np.arange(10.0, K['breath'] - 0.1, 2.0):   # additive: one more note per bar, until the breath
    bar += 1; pattern_bar(t0, min(8, bar + 2), 0.46 + 0.02 * bar)
# S7 subtractive: one note left, then the digits
ev(K['num'], 'marimba', 'A4', 0.4, 0.45)
for t, p in zip(TL['LOCKS'][::-1][:3], ['A5', 'C6', 'E6']):
    ev(t, 'marimba', p, 0.4, 0.55, gain=0.9)
ev(TL['LOCKS'][0], 'glockenspiel', 'E7', 1.2, 0.4, gain=0.7)
ev(K['num'] + 1.5, 'marimba', 'A4', 0.4, 0.45); ev(K['num'] + 2.5, 'marimba', 'A4', 0.4, 0.5); ev(K['facade'], 'marimba', 'E5', 0.4, 0.55); ev(K['num'] + 3.5, 'marimba', 'D5', 0.4, 0.5)
# S8 returns, S9 densest (vibes double an octave up)
for t0 in [K['signs'], K['signs'] + 2]: pattern_bar(t0, 8, 0.6)
for t0 in [K['digi'], K['digi'] + 2]:
    pattern_bar(t0, 8, 0.62); pattern_bar(t0, 8, 0.3, 'vibraphone_hard', 1, 0.6)

# bowed vibraphone pad (real instrument, the pad's job): one soft chord per 4 s, S4–S7
PADS = [(t, [['A3', 'E4', 'G4', 'C5'], ['A3', 'D4', 'F#4', 'B4']][j % 2]) for j, t in enumerate(np.arange(9.5, K['breath'] - 1.0, 4.0))]
for t0, ch in PADS:
    for p in ch: ev(t0, 'vibraphone_bowed', p, 3.9, 0.3, pan=R.uniform(-0.3, 0.3), attack=0.6, release=0.5, gain=0.55)
for p in ['A3', 'E4', 'B4']: ev(K['num'], 'vibraphone_bowed', p, 3.8, 0.28, attack=0.5, release=0.6, gain=0.5)
# bass (jazz double bass) from S5: A / D every two bars; walking in S8–S9
def bass(t, p, v=0.62, d=0.5): ev(t, 'jazz_bass', p, d, v, gain=1.0)
for t0 in np.arange(K['print'], K['breath'] - 0.1, 2.0):
    root = 'A2' if int((t0 - K['print']) // 4) % 2 == 0 else 'D2'
    bass(t0, root); bass(t0 + 1.0, 'E2' if root == 'A2' else 'A2', 0.55)
for t0 in [K['signs'], K['signs'] + 2, K['digi'], K['digi'] + 2]:
    for k, p in enumerate(['A2', 'C3', 'D3', 'E3'] if t0 in (K['signs'], K['digi']) else ['D3', 'C3', 'B2', 'G2']):
        bass(t0 + k * 0.5, p, 0.58)

# picture hits on notes (glockenspiel, soft): tabs, chips, landings, web blocks
for t, p in zip(TL['TABS'], ['E6', 'A6', 'B6', 'E7']): ev(t, 'glockenspiel', p, 0.8, 0.28, gain=0.6)
for t, p in zip(TL['CHIPS'], ['A6', 'B6', 'C7', 'D7', 'E7']): ev(t, 'glockenspiel', p, 0.8, 0.26, gain=0.55)
for t, p in zip(TL['LAND'], ['A6', 'C7', 'E7']): ev(t, 'glockenspiel', p, 1.0, 0.34, gain=0.65)
for t, p in zip(TL['BLOCKS'], ['A6', 'B6', 'C7', 'E7', 'D7', 'A7']): ev(t, 'glockenspiel', p, 0.6, 0.22, gain=0.5)

# S10 the one chord everything lands on: A major add9
SN = K['snap']
for p in ['A3', 'E4', 'B4', 'C#5', 'E5']: ev(SN, 'marimba', p, 1.2, 0.62, pan=R.uniform(-0.4, 0.4))
for p in ['A4', 'C#5', 'E5', 'B5']: ev(SN, 'vibraphone_hard', p, 2.5, 0.45, pan=R.uniform(-0.5, 0.5), gain=0.7)
for p in ['A3', 'C#4', 'E4', 'B4']: ev(SN, 'vibraphone_bowed', p, 2.8, 0.4, attack=0.15, release=0.6, gain=0.75)
ev(SN, 'glockenspiel', 'A6', 2.0, 0.45, release=1.5); ev(SN, 'glockenspiel', 'E7', 2.0, 0.35, release=1.5)
ev(SN, 'jazz_bass', 'A1', 2.0, 0.75, gain=1.3)
# soft pulse under L10 (process continues in A major, quarter notes)
for k in range(5): ev(SN + 0.5 + k * 0.5, 'marimba', ['E5', 'C#5', 'B4', 'C#5', 'A4'][k], 0.4, 0.35)

# S11 subtraction: one note removed per retracting tile, descending
for t, p in zip(TL['RETRACT'], ['E6', 'C#6', 'B5', 'A5', 'E5', 'C#5', 'B4', 'A4', 'E4', 'C#4', 'B3']):
    ev(t, 'marimba', p, 0.35, 0.42 - 0.02 * TL['RETRACT'].index(t), gain=0.85)
# end card: the last A rings out
EN = K['end']
ev(EN, 'marimba', 'A3', 2.5, 0.55); ev(EN, 'glockenspiel', 'A6', 3.0, 0.32, release=3.0)
for p in ['A3', 'E4', 'C#5', 'B4']: ev(EN + 0.02, 'vibraphone_bowed', p, 3.6, 0.32, attack=0.4, release=0.8, gain=0.6)
ev(EN, 'jazz_bass', 'A1', 2.5, 0.6, gain=1.2)
ev(K['end'] + 2.0, 'vibraphone', 'E5', 2.0, 0.25, gain=0.6); ev(K['end'] + 2.0, 'vibraphone', 'A4', 2.0, 0.25, gain=0.6)

EV.sort(key=lambda e: e['t'])
mix = S.render(EV, dur=DUR, master=False)
mix = S.room(mix, size=0.38, mix=0.16)
# digital zero windows: the freeze and the breath (sample-accurate, after reverb)
def zero(a, b, fade=0.006):
    i, j = int(a * SR), int(b * SR); mix[i:j] = 0
    f = int(fade * SR); mix[i - f:i] *= np.linspace(1, 0, f)[:, None]
zero(K['freeze'], K['click'] - 0.004); zero(K['breath'], K['num'] - 0.004)
# end: fade to zero by DUR
f0, f1 = int((DUR - 1.2) * SR), N; mix[f0:f1] *= np.linspace(1, 0, f1 - f0)[:, None] ** 2
mix = mix[:N]
pk = np.abs(mix).max(); mix = mix / pk * 0.89
sf.write(os.path.join(HERE, 'score.wav'), mix.astype(np.float32), SR)
used = sorted({e['inst'] for e in EV})
open(os.path.join(HERE, 'CREDITS_music.txt'), 'w').write('Instruments: ' + ', '.join(used) + '\n' + '\n'.join(S.credits(used)) + '\n')
print('score.wav', DUR, 's,', len(EV), 'notes,', used)
