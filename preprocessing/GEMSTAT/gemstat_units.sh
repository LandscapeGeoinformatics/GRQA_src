#!/bin/bash

#SBATCH --job-name=gemstat_units
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=gemstat_units_%j.out
#SBATCH --error=gemstat_units_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/GEMSTAT

# Load Python
module load python/3.10.10

# Input argument
raw_dir=$1

# Submit the Python script with a micromamba env
micromamba run -n hpc python gemstat_units.py $raw_dir
