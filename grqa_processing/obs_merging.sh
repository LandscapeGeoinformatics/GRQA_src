#!/bin/bash

#SBATCH -p amd
#SBATCH -J obs_merging
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -t 20:00:00
#SBATCH --mem=256G

# cd /gpfs/space/home/holgerv/gis_holgerv/river_quality/scripts/grqa_processing
cd /gpfs/terra/export/samba/gis/holgerv/river_quality/scripts/grqa_processing

module purge
# module load python-3.7.1
module load python

source activate river_quality

# code_file="/gpfs/space/home/holgerv/gis_holgerv/river_quality/data/GRQA/meta/GRQA_param_codes.txt"
# code_file="/gpfs/terra/export/samba/gis/holgerv/GRQA_v1.3/GRQA_meta/GRQA_param_codes.txt"
# readarray param_codes < ${code_file}
# param_code=${param_codes[$SLURM_ARRAY_TASK_ID]}
param_code="TEMP"

~/.conda/envs/river_quality/bin/python obs_merging.py ${param_code}
