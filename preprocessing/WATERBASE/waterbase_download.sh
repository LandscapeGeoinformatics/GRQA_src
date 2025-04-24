#!/bin/bash

#SBATCH --job-name=waterbase_download
#SBATCH --time=01:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=waterbase_download_%j.out
#SBATCH --error=waterbase_download_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/WATERBASE

# Load Python
module load python/3.10.10

# Output directory
out_dir=$1

# Submit the Python script with a micromamba env
micromamba run -n hpc python waterbase_download.py $out_dir
