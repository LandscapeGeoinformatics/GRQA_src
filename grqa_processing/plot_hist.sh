#!/bin/bash

#SBATCH --job-name=plot_hist
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --array=0-42
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=plot_hist_%A_%a.out
#SBATCH --error=plot_hist_%A_%a.err

cd /gpfs/helios/home/holgerv/GRQA_src/grqa_processing

# Load Python
module load python/3.10.10

# Project directory
proj_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa

# Get parameter code
code_file=${proj_dir}/final/GRQA_meta/GRQA_param_codes.txt
readarray param_codes < ${code_file}
param_code=${param_codes[$SLURM_ARRAY_TASK_ID]}

# Submit the Python script with a micromamba env
micromamba run -n hpc python plot_hist.py $proj_dir $param_code
