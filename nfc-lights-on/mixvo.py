import subprocess, os, sys
P = os.path.dirname(os.path.abspath(__file__))
VOL = sys.argv[1] if len(sys.argv) > 1 else '0dB'
f = ["[0:a]aresample=44100,adelay=600:all=1,apad=whole_dur=29,highpass=f=80,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=0.1:ratio=3:attack=5:release=120,pan=stereo|c0=c0|c1=c0,asplit[vo][sc]",
     "[1:a]volume=0.25[m0];[m0][sc]sidechaincompress=threshold=0.03:ratio=8:attack=10:release=300[md]",
     f"[vo]volume=1.6[v];[v][md]amix=inputs=2:normalize=0,volume={VOL},alimiter=limit=0.89:level=false[a]"]
subprocess.run(['ffmpeg','-y','-v','error','-i',f'{P}/assets/vo.wav','-i',f'{P}/out/sfx.wav','-i',f'{P}/out/silent.mp4','-filter_complex',';'.join(f),
  '-map','2:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t','29','-movflags','+faststart',f'{P}/out/elegance-nfc-lights-on-vo.mp4'],check=True)
