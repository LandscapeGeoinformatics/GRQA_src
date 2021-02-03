#!/bin/bash

#SBATCH -p main
#SBATCH -J wqp_preprocessing
#SBATCH -N 4
#SBATCH --ntasks-per-node=4
#SBATCH -t 01:00:00
#SBATCH --mem=128G
#SBATCH --array=0-40

# Name of the dataset
ds_name="WQP"

cd /gpfs/space/home/holgerv/gis_holgerv/river_quality/scripts/preprocessing/${ds_name}

module purge
module load python-3.7.1

source activate river_quality

code_map="/gpfs/space/home/holgerv/gis_holgerv/river_quality/data/${ds_name}/raw/meta/${ds_name}_code_map.txt"
param_codes=($(tail -n +2 ${code_map} | awk -F '\t' '{print $1;}'))
param_code=${param_codes[$SLURM_ARRAY_TASK_ID]}

~/.conda/envs/river_quality/bin/python wqp_preprocessing.py ${param_code}
