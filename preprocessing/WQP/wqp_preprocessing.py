# Import the libraries
import datetime
import os
import pandas as pd
import numpy as np
import sys
import pyproj
import hashlib

# Function for stripping whitespace from string columns
def strip_whitespace(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    return df

# Function for replacing semicolons and line breaks
def replace_chars(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(';', ',')
            df[col] = df[col].str.replace('\n', '')
            df[col] = df[col].str.replace('\r', ' ')
    return df

# Function to check if the date is valid
def check_date(row, date_col):
    correct_date = False
    date_strings = str(row[date_col]).split('-')
    if len(date_strings) >= 3:
        year, month, day = int(date_strings[0]), int(date_strings[1]), int(date_strings[2])
        datetime.datetime(year, month, day)
        correct_date = True
    else:
        print(f'Date error at row {row.name}')
        print(row)
        print('\n')
    return correct_date

# Function for creating dictionary containing file information
def get_file_info(file_path, row_count, file_desc, sheet_name=None):
    info_dict = {}
    info_dict['File name'] = os.path.basename(file_path)
    info_dict['Size (MB)'] = round(int(os.path.getsize(file_path)) / (1024 * 1024), 1)
    info_dict['Rows'] = row_count
    info_dict['Description'] = file_desc
    if sheet_name:
        info_dict['Sheet name'] = sheet_name
    return info_dict

# Function for creating DF of missing values
def get_missing_values(df, file_name, sheet_name=None):
    mv_df = df.isnull().sum(axis=0).reset_index()
    mv_df.columns = ['Column name', 'Missing values']
    mv_df['File name'] = os.path.basename(file_name)
    mv_df = mv_df[['File name', 'Column name', 'Missing values']]
    if sheet_name:
        mv_df['Sheet name'] = sheet_name
        mv_df = mv_df[['File name', 'Sheet name', 'Column name', 'Missing values']]
    return mv_df

# Function for getting statistics of water quality parameter time series
def get_param_stats(value_col, date_col):
    stats_dict = {}
    stats_dict['count'] = value_col.count()
    stats_dict['min'] = value_col.min()
    stats_dict['max'] = value_col.max()
    stats_dict['mean'] = value_col.mean()
    stats_dict['median'] = value_col.median()
    stats_dict['std'] = value_col.std()
    year_col = date_col.str.split('-').str[0]
    year_col = year_col.astype(int)
    stats_dict['min_year'] = year_col.min()
    stats_dict['max_year'] = year_col.max()
    stats_dict['ts_length'] = stats_dict['max_year'] - stats_dict['min_year']
    return pd.Series(
        stats_dict, index=['count', 'min', 'max', 'mean', 'median', 'std', 'min_year', 'max_year', 'ts_length']
    )

# Function for getting a DF with parameter statistics
def get_stats_df(df, groupby_cols, value_col, date_col):
    stats_df = df.groupby(groupby_cols)\
        .apply(lambda group: get_param_stats(group[value_col], group[date_col]))\
        .reset_index()
    for col in ['count', 'min_year', 'max_year', 'ts_length']:
        stats_df[col] = stats_df[col].astype(np.int32)
    return stats_df

# Name of the dataset
ds_name = 'WQP'

# Get parameter code
param_code = sys.argv[1]

# Directory paths
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
raw_dir = os.path.join(proj_dir, 'data', ds_name, 'raw')
proc_dir = os.path.join(proj_dir, 'data', ds_name, 'processed')

# Download directory
dl_dir = os.path.join(raw_dir, 'download_2020-11-16')

# Import the code map
cmap_file = os.path.join(raw_dir, 'meta', ds_name + '_code_map.txt')
cmap_dtypes = {
    'source_param_code': object,
    'param_code': object,
    'source_param_name': object,
    'param_name': object,
    'source_param_form': object,
    'param_form': object,
    'param_code': object,
    'source_unit': object,
    'conversion_constant': np.float64,
    'unit': object,
    'source': object
}
cmap_df = pd.read_csv(cmap_file, sep='\t', usecols=cmap_dtypes.keys(), dtype=cmap_dtypes, encoding='utf-8')
param_codes = cmap_df['source_param_code'].to_list()

# Import site data
site_file = os.path.join(dl_dir, '_'.join([ds_name, param_code, 'sites.csv']))
site_dtypes = {
    'MonitoringLocationIdentifier': object,
    'MonitoringLocationName': object,
    'MonitoringLocationTypeName': object,
    'DrainageAreaMeasure/MeasureValue': np.float64,
    'DrainageAreaMeasure/MeasureUnitCode': object,
    'LatitudeMeasure': np.float64,
    'LongitudeMeasure': np.float64
}
site_df = pd.read_csv(site_file, sep=',', usecols=site_dtypes.keys(), dtype=site_dtypes, quotechar='"')
if len(site_df) < 1:
    sys.exit()
site_df = strip_whitespace(site_df)
site_df = replace_chars(site_df)
site_df.drop_duplicates(inplace=True)
site_df.reset_index(drop=True, inplace=True)

# Get site file information and append to list
info_dicts = []
info_dicts.append(get_file_info(site_file, len(site_df), 'Sampling location data'))

# Get missing values and append to list
mv_dfs = []
mv_dfs.append(get_missing_values(site_df, site_file))

# Drop sites with missing or implausible location information
site_df.drop(site_df[(site_df['MonitoringLocationIdentifier'].isnull())].index, inplace=True, errors='ignore')
site_df.drop(
    site_df[(site_df['LatitudeMeasure'].isnull()) & (site_df['LongitudeMeasure'].isnull())].index, inplace=True,
    errors='ignore'
)
site_df.drop(
    site_df[(site_df['LatitudeMeasure'] < -90) & (site_df['LatitudeMeasure'] > 90)].index, inplace=True,
    errors='ignore'
)
site_df.drop(
    site_df[(site_df['LongitudeMeasure'] < -180) & (site_df['LongitudeMeasure'] > 180)].index, inplace=True,
    errors='ignore'
)

# Get duplicate sites and export to CSV
dup_sites = site_df[site_df.duplicated(['MonitoringLocationIdentifier'])]['MonitoringLocationIdentifier'].to_list()
dup_df = site_df.loc[site_df['MonitoringLocationIdentifier'].isin(dup_sites)]\
    .sort_values('MonitoringLocationIdentifier')
if len(dup_df) > 1:
    dup_df.to_csv(
        os.path.join(proc_dir, 'meta', ds_name + param_code + '_dup_sites.csv'), sep=';', index=False,
        encoding='utf-8'
    )
    # Keep first instance of duplicate site ID
    site_df.drop_duplicates(subset='MonitoringLocationIdentifier', keep='first', inplace=True)
    site_df.reset_index(drop=True, inplace=True)

# Convert coordinates from NAD83 to WGS84
transformer = pyproj.Transformer.from_crs('epsg:4269', 'epsg:4326')
points = list(zip(site_df['LongitudeMeasure'], site_df['LatitudeMeasure']))
coords_wgs = np.array(list(transformer.itransform(points)))
site_df['lon_wgs84'] = coords_wgs[:, 0]
site_df['lat_wgs84'] = coords_wgs[:, 1]
site_df.drop(
    site_df[(site_df['lat_wgs84'].isnull()) & (site_df['lon_wgs84'].isnull())].index, inplace=True, errors='ignore'
)
site_df.drop(
    site_df[(site_df['lat_wgs84'] < -90) & (site_df['lat_wgs84'] > 90)].index, inplace=True, errors='ignore'
)
site_df.drop(
    site_df[(site_df['lon_wgs84'] < -180) & (site_df['lon_wgs84'] > 180)].index, inplace=True, errors='ignore'
)

# Import observation data
obs_file = os.path.join(dl_dir, '_'.join([ds_name, param_code, 'obs.csv']))
obs_dtypes = {
    'ActivityStartDate': object,
    'ActivityStartTime/Time': object,
    'ActivityStartTime/TimeZoneCode': object,
    'MonitoringLocationIdentifier': object,
    'CharacteristicName': object,
    'ResultSampleFractionText': object,
    'ResultMeasureValue': np.float64,
    'ResultMeasure/MeasureUnitCode': object,
    'ResultStatusIdentifier': object,
    'ResultValueTypeName': object,
    'ResultCommentText': object,
    'USGSPCode': object,
    'ResultAnalyticalMethod/MethodName': object,
    'ResultLaboratoryCommentText': object
}
obs_reader = pd.read_csv(obs_file, sep=',', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000, quotechar='"')

# Process observation data in chunks
obs_row_count = 0
obs_chunks = []
for obs_chunk in obs_reader:
    obs_row_count += len(obs_chunk)
    obs_chunk = strip_whitespace(obs_chunk)
    obs_chunk = replace_chars(obs_chunk)
    obs_chunk.drop_duplicates(inplace=True)
    obs_chunk.reset_index(drop=True, inplace=True)
    # Drop missing or negative values
    obs_chunk.drop(
        obs_chunk[(obs_chunk['ResultMeasureValue'].isnull()) | (obs_chunk['ResultMeasureValue'] <= 0)].index,
        inplace=True, errors='ignore'
    )
    obs_chunks.append(obs_chunk)

# DF of observations
obs_df = pd.concat(obs_chunks)
obs_df.drop_duplicates(inplace=True)
obs_df.reset_index(drop=True, inplace=True)
info_dicts.append(get_file_info(obs_file, obs_row_count, 'Water chemistry observations'))
mv_dfs.append(get_missing_values(obs_df, obs_file))

# Create observation identifier column by hashing
df_string = obs_df.to_string(header=False, index=False, index_names=False).split('\n')
obs_strings = ['\t'.join(string.split()) for string in df_string]
hash_ids = [hashlib.sha256(string.encode()).hexdigest() for string in obs_strings]
obs_df['obs_id'] = hash_ids

# Convert date to correct format and add time column
obs_df['obs_date'] = pd.to_datetime(obs_df['ActivityStartDate'], format='%Y-%m-%d', errors='coerce').dt.strftime('%Y-%m-%d')
obs_df['obs_time'] = pd.to_datetime(obs_df['ActivityStartTime/Time'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
obs_df.drop(obs_df[(obs_df['obs_date'].isnull())].index, inplace=True, errors='ignore')

# Check the validity of the dates and drop invalid dates
obs_df['valid_date'] = obs_df.apply(check_date, date_col='obs_date', axis=1)
obs_df = obs_df[obs_df['valid_date']]

# Export file information to CSV
info_df = pd.DataFrame(info_dicts)
info_df.to_csv(
    os.path.join(proc_dir, 'meta', ds_name + '_' + param_code + '_file_info.csv'), sep=';', index=False,
    encoding='utf-8'
)

# Export missing values to CSV
mv_df = pd.concat(mv_dfs)
mv_df.to_csv(
    os.path.join(proc_dir, 'meta', ds_name + '_' + param_code + '_missing_values.csv'), sep=';', index=False,
    encoding='utf-8'
)

# Merge the DFs
merged_df = site_df\
    .merge(obs_df, how='left', on='MonitoringLocationIdentifier')\
    .merge(
        cmap_df, how='left', left_on='USGSPCode',
        right_on='source_param_code'
    )
if len(merged_df) < 1:
    sys.exit()
merged_df.drop_duplicates(inplace=True)
merged_df.reset_index(drop=True, inplace=True)
merged_df.drop(merged_df[(merged_df['param_code'].isnull())].index, inplace=True, errors='ignore')
merged_df.drop(merged_df[(merged_df['obs_date'].isnull())].index, inplace=True, errors='ignore')

# Convert observation values
merged_df['obs_value'] = merged_df['ResultMeasureValue'] * merged_df['conversion_constant']

# Add filtration column
try:
    merged_df.loc[merged_df['ResultSampleFractionText'] == 'Total', 'filtration'] = 'unfiltered'
    merged_df.loc[merged_df['ResultSampleFractionText'] == 'Dissolved', 'filtration'] = 'filtered'
except Exception:
    pass

# # Get statistics about raw and processed observation values and export to CSV
# value_dict = {'raw': 'ResultMeasureValue', 'processed': 'obs_value'}
# for value_type, value_col in value_dict.items():
    # stats_df = get_stats_df(
        # merged_df,
        # ['source_param_code', 'param_code', 'param_name', 'source_param_form', 'param_form', 'source_unit', 'unit'],
        # value_col, 'obs_date'
    # )
    # agg_stats_df = get_stats_df(
        # merged_df, ['MonitoringLocationIdentifier', 'source_param_code'], value_col, 'obs_date'
    # )
    # agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
        # .agg(
            # site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'),
            # mean_ts_length_per_site=('ts_length', 'mean')
        # ).reset_index()
    # stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
    # fname = '_'.join([ds_name, param_code, value_type, 'stats.csv'])
    # stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-16')

# Get statistics about raw observation values and export to CSV
stats_df = get_stats_df(
    merged_df, ['source_param_code', 'param_code', 'source_param_name', 'source_unit'],
    'ResultMeasureValue', 'obs_date'
)
agg_stats_df = get_stats_df(merged_df, ['MonitoringLocationIdentifier', 'source_param_code'], 'ResultMeasureValue', 'obs_date')
agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
    .agg(
        site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'), mean_ts_length_per_site=('ts_length', 'mean')
    )\
    .reset_index()
stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
fname = '_'.join([ds_name, param_code, 'raw', 'stats.csv'])
stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Get statistics about processed observation values and export to CSV
stats_df = get_stats_df(
    merged_df, ['source_param_code', 'param_code', 'source_param_name', 'source_unit'],
    'ResultMeasureValue', 'obs_date'
)
agg_stats_df = get_stats_df(merged_df, ['MonitoringLocationIdentifier', 'source_param_code'], 'ResultMeasureValue', 'obs_date')
agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
    .agg(
        site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'), mean_ts_length_per_site=('ts_length', 'mean')
    )\
    .reset_index()
stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
fname = '_'.join([ds_name, param_code, 'processed', 'stats.csv'])
stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Export processed data to CSV (the output folder should be empty)
meta_cols = ['ResultAnalyticalMethod/MethodName', 'ResultLaboratoryCommentText']
output_codes = merged_df['param_code'].unique()
for code in output_codes:
    code_df = merged_df[merged_df['param_code'] == code]
    # Dictionary with output columns
    code_dict = {
        'obs_id': code_df['obs_id'],
        'lat_wgs84': code_df['lat_wgs84'],
        'lon_wgs84': code_df['lon_wgs84'],
        'obs_date': code_df['obs_date'],
        'obs_time': code_df['obs_time'],
        'obs_time_zone': code_df['ActivityStartTime/TimeZoneCode'],
        'site_id': code_df['MonitoringLocationIdentifier'],
        'site_name': code_df['MonitoringLocationName'],
        'site_country': 'United States',
        'upstream_basin_area': code_df['DrainageAreaMeasure/MeasureValue'],
        'upstream_basin_area_unit': code_df['DrainageAreaMeasure/MeasureUnitCode'],
        'drainage_region_name': np.nan,
        'param_code': code_df['param_code'],
        'source_param_code': code_df['source_param_code'],
        'param_name': code_df['param_name'],
        'source_param_name': code_df['source_param_name'],
        'obs_value': code_df['obs_value'],
        'source_obs_value': code_df['ResultMeasureValue'],
        'param_form': code_df['param_form'],
        'source_param_form': code_df['source_param_form'],
        'unit': code_df['unit'],
        'source_unit': code_df['source_unit'],
        'filtration': code_df['filtration'],
        'source': ds_name
    }
    # Add metadata columns to the dictionary
    for col in meta_cols:
        col_name = '_'.join([ds_name, 'meta', col])
        col_name = col_name.replace('/', '_')
        code_dict[col_name] = code_df[col]
    output_df = pd.DataFrame(code_dict)
    output_fname = os.path.join(proc_dir, code + '_' + ds_name + '.csv')
    if not os.path.isfile(output_fname):
        output_df.to_csv(output_fname, header=output_df.columns, sep=';', index=False, encoding='utf-8')
    else:
        output_df.to_csv(output_fname, mode='a', header=False, sep=';', index=False, encoding='utf-8')
