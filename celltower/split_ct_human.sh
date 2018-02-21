#!/bin/sh

species=human
n=10

python sraify.py < ct_${species}_sc.manifest | \
    awk "{ln += 1; print > sprintf(\"ct_${species}_sc_part%02d.manifest\", (ln % ${n})+1)}"

for i in 01 02 03 04 05 06 07 08 09 10 ; do
    AZ=`python -c "import random; print(random.choice('ABCDEF'))"`
    sed "s/XY/${i}/" < ct_${species}_sc_go_partXY.sh | sed "s/YX/${AZ}/" > ct_${species}_sc_go_part${i}.sh
done
