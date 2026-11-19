"""Place each voiceover sentence on its scene, duck music under voice, keep original ad audio at 39–48 s."""
import subprocess, os
P = os.path.dirname(os.path.abspath(__file__))
# (start in vo.wav, end in vo.wav, target start in video, tempo)
CH = [(0.00, 2.46, 0.50, 1.00),   # hook
      (2.94, 9.35, 4.10, 1.08),   # script
      (9.67, 14.95, 10.40, 1.00), # storyboard
      (15.14, 20.74, 16.25, 1.00),# assets
      (21.07, 29.24, 22.10, 1.04),# animation
      (29.20, 33.57, 30.30, 1.00),# audio & sync
      (34.10, 38.75, 35.00, 1.15),# export
      (39.21, 42.47, 47.95, 1.18)]# end card
PRE, POST = .06, .12
f = []
for i, (a, b, t, k) in enumerate(CH):
    d = (b - a + PRE + POST) / k
    f.append(f"[0:a]atrim={max(0,a-PRE):.3f}:{b+POST:.3f},asetpts=PTS-STARTPTS,atempo={k},afade=t=in:d=0.03,afade=t=out:st={d-0.08:.3f}:d=0.08,adelay={int(t*1000)}:all=1[c{i}]")
    print(f'sentence {i+1}: {t:.2f} -> {t+d:.2f}')
f.append("".join(f"[c{i}]" for i in range(len(CH))) + f"amix=inputs={len(CH)}:normalize=0,aresample=44100,apad=whole_dur=51,highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120,pan=stereo|c0=c0|c1=c0,asplit[vo][sc]")
f.append("[1:a]volume='if(between(t,39.3,47.7),0.15,if(between(t,38.8,39.3),1-(t-38.8)/0.5*0.85,if(between(t,47.7,48.2),0.15+(t-47.7)/0.5*0.85,1)))':eval=frame,volume=0.5[m0]")
f.append("[m0][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md]")
f.append("[2:a]aresample=44100,afade=t=in:d=0.4,afade=t=out:st=8.4:d=0.6,adelay=39000|39000,apad=whole_dur=51[o]")
f.append("[vo]volume=1.6[v];[v][md][o]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=9[a]")
subprocess.run(['ffmpeg','-y','-v','error','-i',f'{P}/assets/vo.wav','-i',f'{P}/out/ambient.wav','-ss','14','-t','9','-i',f'{P}/assets/final.mp4',
  '-i',f'{P}/out/silent.mp4','-filter_complex',';'.join(f),'-map','3:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t','51','-movflags','+faststart',
  f'{P}/out/elegance-making-of-motion-ad-vo.mp4'],check=True)
