#!/bin/bash

#SBATCH -p main
#SBATCH -J plot_sites
#SBATCH -N 4
#SBATCH --ntasks-per-node=4
#SBATCH -t 01:00:00
#SBATCH --mem=256G
#SBATCH --array=0-44

cd /gpfs/space/home/holgerv/gis_holgerv/river_quality/scripts/grqa_processing

module purge
module load python-3.7.1

source activate river_quality

code_file="/gpfs/space/home/holgerv/gis_holgerv/river_quality/data/GRQA/meta/GRQA_param_codes.txt"
readarray param_codes < ${code_file}
param_code=${param_codes[$SLURM_ARRAY_TASK_ID]}

~/.conda/envs/river_quality/bin/python plot_sites.py ${param_code}
