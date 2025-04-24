#!/bin/bash

#SBATCH --job-name=waterbase_preprocessing
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=waterbase_preprocessing_%j.out
#SBATCH --error=waterbase_preprocessing_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/WATERBASE

# Load Python
module load python/3.10.10

# Input arguments
proc_dir=$1
cmap_file=$2
site_file=$3
param_file=$4
obs_file=$5

# Submit the Python script with a micromamba env
micromamba run -n hpc python waterbase_preprocessing.py $proc_dir $cmap_file $site_file $param_file $obs_file