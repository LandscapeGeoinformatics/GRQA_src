#!/bin/bash

#SBATCH --job-name=gemstat_preprocessing
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=holger.virro@ut.ee
#SBATCH --output=gemstat_preprocessing_%j.out
#SBATCH --error=gemstat_preprocessing_%j.err

cd /gpfs/helios/home/holgerv/GRQA_src/preprocessing/GEMSTAT

# Load Python
module load python/3.10.10

# Input arguments
proc_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa/working/GRQA_source_data/GEMSTAT/processed
raw_dir=/gpfs/terra/export/samba/gis/landscape_geoinfo/2021_grqa/original/GRQA_source_data/GEMSTAT/raw
cmap_file=${raw_dir}/meta/GEMSTAT_code_map.csv
site_file=${raw_dir}/GFQA_v2/GEMStat_station_metadata.csv
param_file=${raw_dir}/GFQA_v2/GEMStat_parameter_metadata.csv
method_file=${raw_dir}/GFQA_v2/GEMStat_methods_metadata.csv

# Submit the Python script with a micromamba env
micromamba run -n hpc python gemstat_preprocessing.py $proc_dir $raw_dir $cmap_file $site_file $param_file $method_file
