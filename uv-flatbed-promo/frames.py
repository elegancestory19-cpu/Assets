"""Cut the raw clips on a 124 BPM grid into numbered 1080x1920 JPEG frames."""
import subprocess, os, glob, json
BPM, FPS = 124, 30
beat = 60 / BPM
# (clip, in-point seconds, start beat, end beat)
SEGS = [
    (30, 3.6, 0, 4),
    (37, 1.0, 4, 8),
    (24, 0.2, 8, 10), (22, 0.5, 10, 12),
    (25, 1.2, 12, 14), (27, 0.2, 14, 16), (29, 4.6, 16, 18), (32, 0.4, 18, 20),
    (28, 1.0, 20, 24), (34, 5.5, 24, 28),
    (35, 4.0, 28, 32), (31, 1.5, 32, 36),
    (38, 0.3, 36, 40),
]
END_BEAT = 50
here = os.path.dirname(os.path.abspath(__file__))
for f in glob.glob(f'{here}/frames/*.jpg'):
    os.remove(f)
fr = lambda b: round(b * beat * FPS)
for clip, tin, b0, b1 in SEGS:
    k, n = fr(b0), fr(b1) - fr(b0)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(tin), '-i', f'{here}/assets/{clip}.mp4',
                    '-vf', 'fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,'
                           'crop=1080:1920,unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.12',
                    '-frames:v', str(n), '-start_number', str(k), '-q:v', '3',
                    f'{here}/frames/f%04d.jpg'], check=True)
total = fr(END_BEAT)
json.dump({'bpm': BPM, 'fps': FPS, 'footageFrames': fr(40), 'totalFrames': total,
           'cuts': sorted({fr(s[2]) for s in SEGS} | {fr(40)})}, open(f'{here}/timing.json', 'w'))
print(len(glob.glob(f'{here}/frames/*.jpg')), 'frames; total', total, total / FPS)
