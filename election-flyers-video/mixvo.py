"""Voiceover chunks placed on the warped scenes; soft music bed under it; fixed gain to -15 LUFS."""
import subprocess, os, sys
P = os.path.dirname(os.path.abspath(__file__))
CH = [(0.00, 36.20, 0.10), (36.50, 39.40, 36.75), (39.45, 44.30, 42.45), (44.40, 49.60, 48.05)]  # (vo start, vo end, video start)
VOL = sys.argv[1] if len(sys.argv) > 1 else '0dB'
f = []
for i, (a, b, t) in enumerate(CH):
    d = b - a
    f.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={d-0.06:.3f}:d=0.06,adelay={int(t*1000)}:all=1[c{i}]")
f.append("".join(f"[c{i}]" for i in range(len(CH))) + "amix=inputs=4:normalize=0,aresample=44100,apad=whole_dur=54,highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120,pan=stereo|c0=c0|c1=c0,asplit[vo][sc]")
f.append("[1:a]volume=0.22[m0];[m0][sc]sidechaincompress=threshold=0.05:ratio=3:attack=30:release=500[md]")
f.append(f"[vo]volume=1.6[v];[v][md]amix=inputs=2:normalize=0,volume={VOL},alimiter=limit=0.89:level=false[a]")
subprocess.run(['ffmpeg','-y','-v','error','-i',f'{P}/assets/vo.wav','-i',f'{P}/out/ambient.wav','-i',f'{P}/out/silent.mp4',
  '-filter_complex',';'.join(f),'-map','2:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t','54','-movflags','+faststart',f'{P}/out/election-tracts-vo.mp4'],check=True)
