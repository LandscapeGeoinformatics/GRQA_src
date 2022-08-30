#!/bin/bash

#SBATCH -p amd
#SBATCH -J glorich_preprocessing
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -t 01:00:00
#SBATCH --mem=64G

# Name of the dataset
ds_name="GLORICH"

# cd /gpfs/space/home/holgerv/gis_holgerv/river_quality/scripts/preprocessing/GLORICH
cd /gpfs/terra/export/samba/gis/holgerv/river_quality/scripts/preprocessing/${ds_name}

module purge
# module load python-3.7.1
module load python

source activate river_quality
~/.conda/envs/river_quality/bin/python glorich_preprocessing.py
