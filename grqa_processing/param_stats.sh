#!/bin/bash

#SBATCH -p main
#SBATCH -J param_stats
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -t 01:00:00
#SBATCH --mem=64G

cd /gpfs/space/home/holgerv/gis_holgerv/river_quality/scripts/grqa_processing

module purge
module load python-3.7.1

source activate river_quality
~/.conda/envs/river_quality/bin/python param_stats.py
