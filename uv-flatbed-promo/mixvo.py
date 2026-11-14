"""Place the voiceover phrases on the scene timing, duck the music, mux -> out/elegance-story-uv-flatbed-vo.mp4"""
import subprocess, os
P = os.path.dirname(os.path.abspath(__file__))
# (speech start, speech end in voiceover.wav, target onset in the video)
CH = [(0.27, 2.67, 0.15), (2.98, 4.29, 2.70), (4.81, 6.54, 4.15), (6.78, 9.85, 6.10),
      (10.59, 11.36, 9.80), (11.91, 12.65, 11.75), (13.27, 14.34, 13.70),
      (14.89, 16.03, 15.60), (16.42, 17.41, 17.55), (18.17, 21.52, 19.75)]
PRE, POST = 0.08, 0.14
f, labs = [], []
for i, (a, b, t) in enumerate(CH):
    d = b - a + PRE + POST
    f.append(f"[0:a]atrim={a-PRE:.3f}:{b+POST:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={d-0.06:.3f}:d=0.06,"
             f"adelay={int((t-PRE)*1000)}:all=1[c{i}]")
    labs.append(f"[c{i}]")
f.append("".join(labs) + f"amix=inputs={len(CH)}:normalize=0,aresample=44100,apad=whole_dur=24.2,"
         "loudnorm=I=-15:TP=-1.5:LRA=7,aresample=44100,pan=stereo|c0=c0|c1=c0,asplit[vo][sc]")
f.append("[1:a]volume=0.55[m];[m][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[md]")
f.append("[vo][md]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{P}/assets/voiceover.wav', '-i', f'{P}/out/music.wav',
                '-i', f'{P}/out/silent.mp4', '-filter_complex', ';'.join(f), '-map', '2:v', '-map', '[a]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', '24.2', '-movflags', '+faststart',
                f'{P}/out/elegance-story-uv-flatbed-vo.mp4'], check=True)
