#!/bin/bash

#SBATCH --job-name=waterbase_units
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=waterbase_units_%j.out
#SBATCH --error=waterbase_units_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/WATERBASE

# Load Python
module load python/3.10.10

# Input arguments
raw_dir=$1
obs_file=$2
param_file=$3

# Submit the Python script with a micromamba env
micromamba run -n hpc python waterbase_units.py $raw_dir $obs_file $param_file