#!/bin/bash

#SBATCH --job-name=glorich_preprocessing
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=glorich_preprocessing_%j.out
#SBATCH --error=glorich_preprocessing_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/GLORICH

# Load Python
module load python/3.10.10

# Input arguments
proc_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa/working/GRQA_source_data/GLORICH/processed
raw_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa/original/GRQA_source_data/GLORICH/raw
cmap_file=${raw_dir}/meta/GLORICH_code_map.csv
site_file=${raw_dir}/download_2020-11-16/Shapefiles_GloRiCh/Shapes_GloRiCh/Sampling_Locations_v1.shp
sname_file=${raw_dir}/download_2020-11-16/sampling_locations.csv
catchment_file=${raw_dir}/download_2020-11-16/catchment_properties.csv
remark_file=${raw_dir}/meta/GLORICH_remark_codes.csv
obs_file=${raw_dir}/download_2020-11-16/hydrochemistry.csv

# Submit the Python script with a micromamba env
micromamba run -n hpc python glorich_preprocessing.py $proc_dir $raw_dir $cmap_file $site_file $sname_file $catchment_file $remark_file $obs_file
