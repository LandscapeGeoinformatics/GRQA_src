# GRQA_src
Scripts used during the creation of the Global River Water Quality Archive (GRQA)

The scripts are divided into two folders. Folder *preprocessing* contains scripts used for preprocessing raw source data into a common structure used for GRQA. Folder *grqa_processing* contains scripts used for processing the merged data, generating plots and statistics.

*preprocessing* contains the following scripts:
* \*\_download used for downloading source data
* \*\_units for collecting water quality parameter units when multiple units per parameter were present in source data
* \*\_preprocessing for source data cleaning and parameter harmonization to convert into a common structure used in GRQA
* WQP\_merge\_stats for merging WQP time series statistics

Each Python script has a corresponding shell script that was used for submitting Slurm jobs on the HPC cluster of University of Tartu.
