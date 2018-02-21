#!/bin/sh

python sraify.py < ct_mouse_sc.manifest | \
    awk '{ln += 1} (ln % 25) < 10 {print > sprintf("ct_mouse_sc_part%02d.manifest", (ln % 25)+1)}'
python sraify.py < ct_mouse_sc.manifest | \
    awk '{ln += 1} (ln % 25) >= 10 {print > sprintf("ct_mouse_sc_part%02d.manifest", (ln % 25)+1)}'

for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 ; do
    AZ=`python -c "import random; print(random.choice('ABCDEF'))"`
    sed "s/XY/${i}/" < ct_mouse_sc_go_partXY.sh | sed "s/YX/${AZ}/" > ct_mouse_sc_go_part${i}.sh
done
