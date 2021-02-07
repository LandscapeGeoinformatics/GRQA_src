# Import the libraries
import sys
import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
import pysal.viz.mapclassify as mc
import collections
import matplotlib.patches as mpatches

# Name of the dataset
ds_name = 'GRQA'

# Source dataset names
sources = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']

# Get parameter code
param_code = sys.argv[1]

# Directory paths
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
data_dir = os.path.join(proj_dir, 'data', ds_name, 'data')
fig_dir = os.path.join(proj_dir, 'data', ds_name, 'figures')

# Import observation data
obs_dtypes = {
    'obs_id': object,
    'site_id': object,
    'lat_wgs84': np.float64,
    'lon_wgs84': np.float64,
    'obs_date': object,
    'obs_value': np.float64,
    'unit': object,
    'obs_iqr_outlier': object,
    'site_ts_availability': np.float64,
    'site_ts_continuity': np.float64,
    'source': object
}
obs_file = os.path.join(data_dir, param_code + '_' + ds_name + '.csv')
obs_reader = pd.read_csv(obs_file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000)
obs_chunks = []
for obs_chunk in obs_reader:
    obs_chunk.drop_duplicates(inplace=True)
    obs_chunks.append(obs_chunk)
obs_df = pd.concat(obs_chunks)
obs_df.drop_duplicates(inplace=True)
obs_df.reset_index(drop=True, inplace=True)

# Percentage of outliers
outlier_count = len(obs_df[obs_df['obs_iqr_outlier'] == 'yes'])
outlier_perc = np.round(outlier_count / obs_df['obs_id'].nunique() * 100, 1)

# Get unit
unit = obs_df['unit'].iloc[0]

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(obs_df, geometry=gpd.points_from_xy(obs_df['lon_wgs84'], obs_df['lat_wgs84']))
gdf = gdf.set_crs('epsg:4326')
gdf['geometry'] = gdf['geometry'].to_crs('+proj=robin')
gdf = gdf.set_crs('+proj=robin')

# Classify availability for plotting
gdf.loc[gdf['site_ts_availability'] < 0.2, 'avail_class'] = '0 - 20%'
gdf.loc[(gdf['site_ts_availability'] > 0.2) & (gdf['site_ts_availability'] < 0.4), 'avail_class'] = '20 - 40%'
gdf.loc[(gdf['site_ts_availability'] > 0.4) & (gdf['site_ts_availability'] < 0.6), 'avail_class'] = '40 - 60%'
gdf.loc[(gdf['site_ts_availability'] > 0.6) & (gdf['site_ts_availability'] < 0.8), 'avail_class'] = '60 - 80%'
gdf.loc[gdf['site_ts_availability'] > 0.8, 'avail_class'] = '80 - 100%'

# Classify continuity for plotting
gdf.loc[gdf['site_ts_continuity'] < 0.2, 'cont_class'] = '0 - 20%'
gdf.loc[(gdf['site_ts_continuity'] > 0.2) & (gdf['site_ts_continuity'] < 0.4), 'cont_class'] = '20 - 40%'
gdf.loc[(gdf['site_ts_continuity'] > 0.4) & (gdf['site_ts_continuity'] < 0.6), 'cont_class'] = '40 - 60%'
gdf.loc[(gdf['site_ts_continuity'] > 0.6) & (gdf['site_ts_continuity'] < 0.8), 'cont_class'] = '60 - 80%'
gdf.loc[gdf['site_ts_continuity'] > 0.8, 'cont_class'] = '80 - 100%'

# Import world map
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world['geometry'] = world['geometry'].to_crs('+proj=robin')

# Plot sites
colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
color_dict = dict(zip(sources, colors))
fig = plt.figure(figsize=(8, 8), facecolor='w')
ax = world.plot(color='lightgrey', edgecolor=None)
ax.set_axis_off()
ax.set_title('Spatial distribution of ' + param_code + ' sites', fontweight='bold', fontname='Arial', fontsize=6)
for source, data in gdf.groupby('source'):
    data.plot(
        ax=ax, marker='.', categorical=True, markersize=2, linewidth=0, legend=True, color=data['source'].map(color_dict),
        label=source
    )
fig.tight_layout()
plt.legend(loc='lower center', ncol=5, bbox_to_anchor=[0.5, -0.04], frameon=False, markerscale=4, fontsize=4)
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_spatial_dist.png'), dpi=300, bbox_inches='tight',
    pad_inches=0
)

# Plot availability of time series
classes = ['0 - 20%', '20 - 40%', '40 - 60%', '60 - 80%', '80 - 100%']
colors = ['#440154', '#3a528b', '#20908d', '#5dc962', '#fde725']
color_dict = dict(zip(classes, colors))
fig = plt.figure(figsize=(8, 8), facecolor='w')
ax = world.plot(color='lightgrey', edgecolor=None)
ax.set_axis_off()
ax.set_title(
    'Monthly time series availability of ' + param_code + ' observations', fontweight='bold', fontname='Arial',
    fontsize=6
)
for cl in classes:
    gdf[gdf['avail_class'] == cl].plot(
        ax=ax, marker='.', column='cl', markersize=2, linewidth=0, legend=True, color=color_dict.get(cl),
        label=cl
    )
fig.tight_layout()
plt.legend(loc='lower center', ncol=5, bbox_to_anchor=[0.5, -0.04], frameon=False, markerscale=4, fontsize=4)
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_availability.png'), dpi=300, bbox_inches='tight',
    pad_inches=0
)

# Plot continuity of time series
classes = ['0 - 20%', '20 - 40%', '40 - 60%', '60 - 80%', '80 - 100%']
colors = ['#440154', '#3a528b', '#20908d', '#5dc962', '#fde725']
color_dict = dict(zip(classes, colors))
fig = plt.figure(figsize=(8, 8), facecolor='w')
ax = world.plot(color='lightgrey', edgecolor=None)
ax.set_axis_off()
ax.set_title(
    'Monthly time series continuity of ' + param_code + ' observations', fontweight='bold', fontname='Arial',
    fontsize=6
)
for cl in classes:
    gdf[gdf['cont_class'] == cl].plot(
        ax=ax, marker='.', column='cl', markersize=2, linewidth=0, legend=True, color=color_dict.get(cl),
        label=cl
    )
fig.tight_layout()
plt.legend(loc='lower center', ncol=5, bbox_to_anchor=[0.5, -0.04], frameon=False, markerscale=4, fontsize=4)
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_continuity.png'), dpi=300, bbox_inches='tight', pad_inches=0
)

# Plot median observation values without outliers
median_df = gdf.groupby('site_id')['obs_value'].median().reset_index()
median_df.columns = ['site_id', 'site_median_obs_value']
gdf = gdf.merge(median_df, on='site_id', how='left')
gdf.drop_duplicates(inplace=True)
gdf.reset_index(drop=True, inplace=True)
gdf.drop(gdf[gdf['obs_iqr_outlier'] == 'yes'].index, inplace=True)
classifier = mc.NaturalBreaks.make(k=5)
gdf['cl'] = gdf[['site_median_obs_value']].apply(classifier)
fig = plt.figure(figsize=(8, 8), facecolor='w')
ax = world.plot(color='lightgrey', edgecolor=None)
ax.set_axis_off()
if outlier_perc != 0.0:
    text = 'Outliers detected by the IQR test ({}% of observations) have been removed'.format(outlier_perc)
    ax.text(0.5, 1, text, ha='center', va='center', transform=ax.transAxes, fontsize=4)
ax.set_title('Median observation values of ' + param_code + ' sites ({})'.format(unit), fontweight='bold', fontname='Arial', fontsize=6)
group_df = gdf.groupby('cl')
legend_dict = collections.OrderedDict([])
colors = ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000']
color_dict = dict(zip(legend_dict.keys(), colors))
cmap = matplotlib.colors.ListedColormap(colors)
for (cl, data), color in zip(group_df, colors):
    min = data['site_median_obs_value'].min()
    max = data['site_median_obs_value'].max()
    legend_dict.update({"{:.2f} - {:.2f}".format(min, max): color})
patches = []
for cl in legend_dict:
    data_key = mpatches.Patch(color=legend_dict[cl], label=cl)
    patches.append(data_key)
for cl in sorted(gdf['cl'].unique()):
    gdf[gdf['cl'] == cl].plot(
        ax=ax, marker='.', column='cl', markersize=2, linewidth=0, color=colors[int(cl)]
    )
ax.legend(loc='lower center', ncol=5, bbox_to_anchor=[0.5, -0.04], frameon=False, handles=patches, fontsize=4)
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_median.png'), dpi=300, bbox_inches='tight', pad_inches=0
)
