# Import the libraries
import os
from datetime import date
import shutil
import urllib.request
import zipfile

# Name of the dataset
ds_name = 'GLORICH'

# Download directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
dl_dir = os.path.join(proj_dir, 'data', ds_name, 'raw', f'download_{date.today()}')
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)

# Download the ZIP
url = 'http://store.pangaea.de/Publications/HartmannJens-etal_2019/Glorich_V01_CSV_plus_Shapefiles_2019_05_24.zip'
response = urllib.request.urlopen(url)
file_path = os.path.join(dl_dir, url.split('/')[-1])
urllib.request.urlretrieve(url, file_path)

# Extract the ZIP
with zipfile.ZipFile(file_path, 'r') as zip_ref:
    zip_ref.extractall(dl_dir)
