#!/bin/bash -l
#SBATCH
#SBATCH --partition=parallel
#SBATCH --nodes=1
#SBATCH --mem=5G
#SBATCH --time=2:00:00
#SBATCH --ntasks-per-node=24

NM=mouseling25
MANIFEST=${NM}.manifest
RAIL="${HOME}/raildotbio"

mkdir -p ${NM}

python ${RAIL}/rail-rna prep local \
    -m ${MANIFEST} \
    -o "${NM}/output" \
    --max-task-attempts 3 \
    --keep-intermediates \
    --log "${NM}/intermediate_log" \
    -p 22

