#!/bin/sh
# One-command rebuild: sh build.sh   (needs the Lemo-Opuscar library at $LIB)
set -e
LIB=${LIB:-/root/lemo-opuscar}; export LIB
HERE=$(cd "$(dirname "$0")" && pwd)
PY=$LIB/.venv/bin/python
cd "$HERE" && node tools/dump.mjs                                   # timeline → timeline.json
$PY "$HERE/music/score.py"                                           # score (real instruments) → music/score.wav
$PY "$HERE/mix.py"                                                   # + client voice (voice/L*.wav), ducking → out/mix.wav
cd "$LIB"
node core/render/readcheck.mjs "$HERE" --size 1080x1920
node core/render/video.mjs "$HERE" --fps 24 --size 1080x1920 --workers 4 --out "$HERE/out/video.mp4"
sh "$HERE/tools/mux.sh" "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/es-keynote.mp4"
node core/render/still.mjs "$HERE" 48 --size 1080x1920 --q nosub=1 --out "$HERE/out/still" --prefix po_ && cp "$HERE/out/still/po_48.jpg" "$HERE/poster.jpg"
