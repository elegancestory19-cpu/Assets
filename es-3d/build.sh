#!/bin/sh
# One-command rebuild: sh build.sh   (needs the Lemo-Opuscar library at $LIB)
set -e
LIB=${LIB:-/root/lemo-opuscar}; export LIB
HERE=$(cd "$(dirname "$0")" && pwd); PY=$LIB/.venv/bin/python
cd "$HERE" && node tools/dump.mjs                                     # story.js → timeline.json + out/srt.json
$PY -I tools/cut_voice.py voice/raw/take1.wav voice/cuts.json          # client voice → voice/L*.wav (silence cuts only)
cd "$LIB" && node core/render/events.mjs "$HERE" --size 1080x1920      # picture events (with notes) → events.json
$PY "$HERE/music/score.py"                                             # event-driven score → music/score.wav
$PY "$HERE/mix.py"                                                     # + voice, ducking → out/mix.wav
$PY core/render/srt.py "$HERE/out/srt.json" "$HERE/es-3d.srt"
node core/render/video.mjs "$HERE" --fps 24 --size 1080x1920 --workers 4 --out "$HERE/out/video.mp4"
sh "$HERE/tools/mux.sh" "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/es-3d.mp4"
node core/render/still.mjs "$HERE" 29.5 --size 1080x1920 --q nohud=1 --out "$HERE/out/still" --prefix po_ && cp "$HERE/out/still/po_29.5.jpg" "$HERE/poster.jpg"
