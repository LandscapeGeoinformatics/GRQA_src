#!/bin/bash

#SBATCH --job-name=plot_sites_grid
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=plot_sites_grid_%j.out
#SBATCH --error=plot_sites_grid_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/grqa_processing

# Load Python
module load python/3.10.10

# Project directory
proj_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa

# Submit the Python script with a micromamba env
micromamba run -n hpc python plot_sites_grid.py $proj_dir
