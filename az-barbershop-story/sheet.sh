#!/bin/bash
P=$(dirname "$(readlink -f "$0")")
mkdir -p "$P/out/shots"; find "$P/out/shots" -name '*.png' -delete
node "$P/render.mjs" shots "$@" 2>&1 | tail -5
python3 - "$P/out/shots" <<'PY'
import sys,glob
from PIL import Image,ImageDraw
d=sys.argv[1]; fs=sorted(glob.glob(d+'/*.png'))
im=Image.new('RGB',(270*6,480*((len(fs)+5)//6)),'gray'); dr=ImageDraw.Draw(im)
for k,f in enumerate(fs):
    x,y=270*(k%6),480*(k//6); im.paste(Image.open(f).resize((270,480)),(x,y))
    for yy in (int(480*.14),int(480*.65)): dr.line([(x,y+yy),(x+270,y+yy)],fill=(255,0,0),width=1)
    dr.text((x+4,y+4),f.split('/')[-1][:-4],fill='yellow')
im.save(d+'/sheet.jpg',quality=85)
PY
