# Import the libraries
import os
from datetime import date
import shutil
import urllib.request

# Name of the dataset
ds_name = 'CESI'

# Download directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
dl_dir = os.path.join(proj_dir, 'data', ds_name, 'raw', f'download_{date.today()}')
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)

# Download CSV files
csv_urls = [
    'https://www.canada.ca/content/dam/eccc/documents/csv/cesindicators/water-quality-canadian-rivers/2020/'
    'table-descriptions-tableau.csv',
    'https://www.canada.ca/content/dam/eccc/documents/csv/cesindicators/water-quality-canadian-rivers/2020/'
    'wqi-federal-raw-data-2020-iqe-donnees-brutes-fed.csv',
    'https://www.canada.ca/content/dam/eccc/documents/csv/cesindicators/water-quality-canadian-rivers/2020/'
    'wqi-federal-trend-data-2020-iqe-donnees-tendance-federal.csv',
    'https://www.canada.ca/content/dam/eccc/documents/csv/cesindicators/water-quality-canadian-rivers/2020/'
    'wqi-iqe-federal-score-2020.csv'
]
for url in csv_urls:
    response = urllib.request.urlopen(url)
    fname = url.split('/')[-1]
    file_path = os.path.join(dl_dir, fname)
    urllib.request.urlretrieve(url, file_path)
