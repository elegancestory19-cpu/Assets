#!/bin/bash
# Mux each silent episode with its music bed -> out/final/day-NN.mp4 (original clip audio is never used)
H=$(dirname "$(readlink -f "$0")")
mkdir -p "$H/out/final"
for v in "$H"/out/silent/ep*.mp4; do
  n=$(basename "$v" .mp4 | sed 's/ep//')
  ffmpeg -y -v error -i "$v" -i "$H/out/music/ep$n.wav" -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$H/out/final/day-$n.mp4"
done
ls "$H/out/final" | wc -l
