#!/bin/bash -l
#SBATCH --output=/dev/null
#SBATCH --error=.marcc_mouseling25_align.sh.out
#SBATCH --partition=parallel
#SBATCH --nodes=1
#SBATCH --mem=120G
#SBATCH --time=96:00:00
#SBATCH --ntasks-per-node=24

# TODO: just record stderr

NM=mouseling25
MANIFEST="${NM}.manifest"
PID_ARGS="--thread-ceiling 22 --thread-piddir /tmp/rail-pid-tmp"
RAIL="${HOME}/raildotbio"

python ${RAIL}/rail-rna align local \
       -m ${MANIFEST} \
       -i "${NM}/preproc" \
       -x /scratch/groups/blangme2/indexes/rail/mm10/index_links/genome \
       -o "${NM}/output" \
       --log "${NM}/align_log" \
       --scratch "/scratch/groups/blangme2/langmead_temp" \
       --drop-deletions \
       -p 22 \
       --max-task-attempts 3 \
       --keep-intermediates
