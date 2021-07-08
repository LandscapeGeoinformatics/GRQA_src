# GRQA_src

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5082148.svg)](https://doi.org/10.5281/zenodo.5082148)

Scripts used during the creation of the Global River Water Quality Archive (GRQA).

The dataset can be downloaded at <http://dx.doi.org/10.23673/re-273>

Preprint of the data description paper is available at <https://essd.copernicus.org/preprints/essd-2021-51/>

The scripts are divided into two folders. Folder **preprocessing** contains scripts used for preprocessing raw source data into a common structure used for GRQA. Folder **grqa_processing** contains scripts used for processing the merged data, generating plots and statistics.

**preprocessing** contains the following scripts:
* *\*\_download* used for downloading source data
* *\*\_units* for collecting water quality parameter units when multiple units per parameter were present in source data
* *\*\_preprocessing* for source data cleaning and parameter harmonization to convert into a common structure used in GRQA
* *WQP\_merge\_stats* for merging WQP time series statistics

**grqa\_preprocessing** contains the following scripts:
* *\*\_param\_codes* for creating a list of GRQA parameters used as an input for the parallel implementation of *\*_obs\_merging*
* *\*\_obs\_merging* used for merging harmonized source data, calculating time series statistics per site (outliers, monthly availability, continuity) and flagging potential duplicate observations
* *\*\_param\_stats* for calculating GRQA time series statistics per parameter
* *\*\_plot\_sites* for creating maps of observation site distribution, monthly availablity, monthly continuity and median value per parameter
* *\*\_plot\_hist* for creating temporal distribution plots, histograms and box plots per parameter
* *\*\_plot\_sites\_grid* for creating maps of observation site distribution, monthly availablity, monthly continuity and median value of DO, DOC, TP and TSS for the paper
* *\*\_plot\_hist\_grid* for creating temporal distribution plots, histograms and box plots of DO, DOC, TP and TSS for the paper

Each Python script has a corresponding shell script that was used for submitting Slurm jobs to the HPC cluster of University of Tartu.
