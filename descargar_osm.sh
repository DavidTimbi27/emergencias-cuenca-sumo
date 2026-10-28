#!/bin/bash
# Descarga el recuadro de Cuenca en 5x5 teselas (API OSM 0.6, limite 50 000 nodos por peticion)
LON_MIN=-79.030; LON_MAX=-78.950
LAT_MIN=-2.930;  LAT_MAX=-2.860
N=5
OUT="$HOME/results/reto/osm"
mkdir -p "$OUT"

for i in $(seq 0 $((N-1))); do
  for j in $(seq 0 $((N-1))); do
    W=$(awk -v a=$LON_MIN -v b=$LON_MAX -v n=$N -v k=$i       'BEGIN{printf "%.6f", a+(b-a)*k/n}')
    E=$(awk -v a=$LON_MIN -v b=$LON_MAX -v n=$N -v k=$((i+1)) 'BEGIN{printf "%.6f", a+(b-a)*k/n}')
    S=$(awk -v a=$LAT_MIN -v b=$LAT_MAX -v n=$N -v k=$j       'BEGIN{printf "%.6f", a+(b-a)*k/n}')
    T=$(awk -v a=$LAT_MIN -v b=$LAT_MAX -v n=$N -v k=$((j+1)) 'BEGIN{printf "%.6f", a+(b-a)*k/n}')
    F="$OUT/tile_${i}_${j}.osm"
    echo ">>> tesela ${i}_${j}  bbox=$W,$S,$E,$T"
    curl -f -sS --retry 3 --retry-delay 5 -A "RVH-UCuenca-reto/1.0" \
      -o "$F" "https://api.openstreetmap.org/api/0.6/map?bbox=$W,$S,$E,$T" \
      || { echo "ERROR en tesela ${i}_${j}"; rm -f "$F"; }
    sleep 2
  done
done
echo "Terminado."
