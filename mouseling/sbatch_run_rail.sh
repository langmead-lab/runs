#!/bin/bash -l
#SBATCH
#SBATCH --partition=parallel
#SBATCH --nodes=1
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --ntasks-per-node=24

# Shared queue:
# --ntasks-per-node=(default: 24, max: 24)
# --mem=(default: 5G, max: 128G)
# --time=(default: 1:00:00, max: 100:00:00)

sh -x run_rail.sh
