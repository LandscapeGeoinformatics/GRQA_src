# Import the libraries
import os
from datetime import date
import shutil
import urllib.request
import zipfile

# Name of the dataset
ds_name = 'WATERBASE'

# Download directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
dl_dir = os.path.join(proj_dir, 'data', ds_name, 'raw', f'download_{date.today()}')
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)

# Download and extract ZIP files
zip_urls = [
    'https://cmshare.eea.europa.eu/s/rdiDRYdK8PgcWzg/download',
    'https://cmshare.eea.europa.eu/s/iQoXKStjwENAQDb/download'
]
for url in zip_urls:
    response = urllib.request.urlopen(url)
    file_path = os.path.join(dl_dir, response.info().get_filename())
    urllib.request.urlretrieve(url, file_path)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(dl_dir)

# Download CSV files
csv_urls = [
    'http://dd.eionet.europa.eu/vocabulary/wise/WFDWaterBodyCategory/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/ObservedProperty/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/Matrix/csv',
    'http://dd.eionet.europa.eu/vocabulary/wise/Uom/csv'
]
for url in csv_urls:
    response = urllib.request.urlopen(url)
    file_path = os.path.join(dl_dir, response.info().get_filename())
    urllib.request.urlretrieve(url, file_path)
