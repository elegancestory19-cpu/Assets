#!/bin/bash
# usage: sheet.sh t1 t2 ...  -> out/shots/sheetN.jpg
P=$(dirname "$(readlink -f "$0")")
node "$P/render.mjs" shots "$@" 2>&1 | tail -5
python3 - "$P/out/shots" <<'PY'
import sys,glob
from PIL import Image
d=sys.argv[1]; fs=sorted(glob.glob(d+'/*.png'))
for g in range((len(fs)+9)//10):
    im=Image.new('RGB',(360*5,640*2))
    for k,f in enumerate(fs[g*10:g*10+10]): im.paste(Image.open(f).resize((360,640)),(360*(k%5),640*(k//5)))
    im.save(f'{d}/sheet{g}.jpg',quality=85)
PY
