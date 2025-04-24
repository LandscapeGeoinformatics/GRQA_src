# Import the libraries
import sys
import os
from datetime import date
import shutil
import urllib.request

# Name of the dataset
ds_name = 'WATERBASE'

# Download directory
out_dir = sys.argv[1]
dl_dir = os.path.join(
    out_dir, f'download_{date.today()}'
)
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)

# Download data files
base_url = (
    'https://sdi.eea.europa.eu/datashare/s/Ckep6QDSb4WygNF/'
    'download?path=&files='
)
data_urls = [
    f'{base_url}/Waterbase_v2023_1_S_WISE6_SpatialObject_DerivedData.csv',
    f'{base_url}/Waterbase_v2023_1_T_WISE6_AggregatedData.csv',
    f'{base_url}/Waterbase_v2023_1_T_WISE6_AggregatedDataByWaterBody.csv',
    f'{base_url}/Waterbase_v2023_1_T_WISE6_DisaggregatedData.csv'
]
for url in data_urls:
    response = urllib.request.urlopen(url)
    file_path = os.path.join(dl_dir, os.path.basename(url))
    urllib.request.urlretrieve(url, file_path)

# Download metadata files
meta_urls = [
    'http://dd.eionet.europa.eu/vocabulary/wise/WFDWaterBodyCategory/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/ObservedProperty/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/Matrix/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/Uom/csv'
]
for url in meta_urls:
    response = urllib.request.urlopen(url)
    file_path = os.path.join(dl_dir, response.info().get_filename())
    urllib.request.urlretrieve(url, file_path)
