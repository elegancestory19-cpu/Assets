"""Voiceover chunks on their scenes + new sound design underneath (ducked), fixed gain to target loudness."""
import subprocess, os, sys
P = os.path.dirname(os.path.abspath(__file__))
CH = [(0.15, 2.75, 0.2), (2.95, 7.72, 2.95), (7.78, 11.88, 8.3), (12.05, 14.62, 12.9), (14.62, 16.6, 15.7), (16.95, 19.75, 18.3)]
VOL = sys.argv[1] if len(sys.argv) > 1 else '0dB'
SFX = sys.argv[2] if len(sys.argv) > 2 else '0.55'
f = []
for i, (a, b, t) in enumerate(CH):
    d = b - a
    f.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.05:.3f}:d=0.05,adelay={int(t*1000)}:all=1[c{i}]")
f.append("".join(f"[c{i}]" for i in range(len(CH))) + f"amix=inputs={len(CH)}:normalize=0,aresample=44100,apad=whole_dur=23.6,highpass=f=80,"
         "equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=0.1:ratio=3:attack=5:release=120,pan=stereo|c0=c0|c1=c0,asplit[vo][sc]")
f.append(f"[1:a]volume={SFX}[m0];[m0][sc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=350[md]")
f.append(f"[vo]volume=1.6[v];[v][md]amix=inputs=2:normalize=0,volume={VOL},alimiter=limit=0.89:level=false[a]")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{P}/assets/vo.wav', '-i', f'{P}/out/sfx2.wav', '-i', f'{P}/out/silent.mp4', '-filter_complex', ';'.join(f),
                '-map', '2:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', '23.6', '-movflags', '+faststart',
                f'{P}/out/elegance-bags-3d-vo.mp4'], check=True)
