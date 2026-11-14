"""Per-episode: extract muted 1080x1920 frames on a beat grid -> frames/<ep>/, write build.json"""
import subprocess, os, json, sys, shutil
H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, '..', 'assets')
eps = json.load(open(f'{H}/episodes.json'))
BPMS = {'cine': [96, 100, 104, 92], 'drive': [120, 116, 124, 112]}
only = set(map(int, sys.argv[1:]))
out = []
for n, e in enumerate(eps, 1):
    bpm = BPMS[e['style']][n % 4]; beat = 60 / bpm
    still = 'still' in e
    speed = e.get('speed', 1)
    avail = 6.5 if still else e['use'] / speed
    lo = 5.0 / beat
    beats = int(max(avail, 5.0) / beat); beats -= beats % 2
    beats = max(beats, int(lo) + int(lo) % 2); beats = min(beats, int(9.5 / beat) // 2 * 2)
    nf = round(beats * beat * 30)
    e.update(ep=n, bpm=bpm, beats=beats, endBeats=6 if e['style'] == 'drive' else 5, nFoot=nf)
    out.append(e)
    if only and n not in only: continue
    d = f'{H}/frames/{n:02d}'; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    vf = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,unsharp=5:5:0.6,eq=contrast=1.06:saturation=1.12'
    src = f"{A}/{e['clip']}.mp4"
    if still:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(e['still']), '-i', src, '-frames:v', '1', '-vf', vf, '-q:v', '2', f'{d}/f0000.jpg']
    else:
        pre = f"setpts=PTS/{speed}," + ("minterpolate=fps=30:mi_mode=blend," if speed < 1 else "") + "fps=30,"
        cmd = ['ffmpeg', '-v', 'error', '-y', '-an', '-ss', str(e['in']), '-t', str(e['use']), '-i', src,
               '-vf', pre + vf + ',tpad=stop_mode=clone:stop_duration=12', '-frames:v', str(nf), '-q:v', '3', f'{d}/f%04d.jpg']
    subprocess.run(cmd, check=True)
    if not still:  # ffmpeg numbers from 1
        fs = sorted(os.listdir(d))
        for i, f in enumerate(fs): os.rename(f'{d}/{f}', f'{d}/g{i:04d}.jpg')
        for i in range(len(fs)): os.rename(f'{d}/g{i:04d}.jpg', f'{d}/f{i:04d}.jpg')
    print(n, e['clip'], bpm, beats, nf, len(os.listdir(d)))
json.dump(out, open(f'{H}/build.json', 'w'), ensure_ascii=False, indent=1)
