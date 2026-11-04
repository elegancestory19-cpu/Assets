#!/bin/sh
# mux + two-pass loudnorm to −14 LUFS / TP −1.2 (works with ffmpeg 6): sh tools/mux.sh video.mp4 mix.wav out.mp4
set -e
V=$1; A=$2; O=$3; T=$(mktemp -d)
J=$(ffmpeg -hide_banner -i "$A" -af loudnorm=I=-14:TP=-1.2:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
set -- $(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -hide_banner -loglevel error -y -i "$A" -af "loudnorm=I=-14:TP=-1.2:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true,aresample=48000" -c:a pcm_s16le "$T/a.wav"
ffmpeg -hide_banner -loglevel error -y -i "$V" -i "$T/a.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$O"
rm -rf "$T"; ffmpeg -hide_banner -i "$O" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
