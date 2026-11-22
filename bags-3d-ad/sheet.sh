#!/bin/bash
# usage: sheet.sh t1 t2 ...  -> out/shots/sheet.jpg (each run writes into its own folder)
P=$(dirname "$(readlink -f "$0")")
RUN="$P/out/shots/run-$(date +%s%N)"; mkdir -p "$RUN"
SHOTDIR="$RUN" node "$P/render.mjs" shots "$@" 2>&1 | tail -5
python3 - "$RUN" <<'PY'
import sys,glob
from PIL import Image,ImageDraw
d=sys.argv[1]; fs=sorted(glob.glob(d+'/*.png')); w,h=270,480
im=Image.new('RGB',(w*6,h*((len(fs)+5)//6)),'gray'); dr=ImageDraw.Draw(im)
for k,f in enumerate(fs):
    x,y=w*(k%6),h*(k//6); im.paste(Image.open(f).resize((w,h)),(x,y)); dr.text((x+4,y+4),f.split('/')[-1][:-4],fill='red')
im.save(d+'/../sheet.jpg',quality=85)
PY
