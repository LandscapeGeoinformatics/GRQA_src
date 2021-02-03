# Import the libraries
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import collections
import matplotlib.patches as mpatches

# Name of the dataset
ds_name = 'GRQA'

# Source dataset names
sources = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']

# Parameter codes
param_codes = ['DO', 'DOC', 'TP', 'TSS']

# Directory paths
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
data_dir = os.path.join(proj_dir, 'data', ds_name, 'data')
fig_dir = os.path.join(proj_dir, 'data', ds_name, 'figures')

# Import observation data
obs_dtypes = {
    'site_id': object,
    'lat_wgs84': np.float64,
    'lon_wgs84': np.float64,
    'obs_date': object,
    'obs_value': np.float64,
    'param_code': object,
    'unit': object,
    'obs_iqr_outlier': object,
    'site_ts_availability': np.float64,
    'site_ts_continuity': np.float64,
    'source': object
}
obs_dfs = []
units = []
outliers = []
for param_code in param_codes:
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
    outlier_perc = np.round(outlier_count / len(obs_df) * 100, 1)
    outliers.append(outlier_perc)
	# Get unit
    unit = obs_df['unit'].iloc[0]
    units.append(unit)
    obs_dfs.append(obs_df)

# Color dictionary
sources = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']
colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
color_dict = dict(zip(sources, colors))

# Create temporal distribution plot
fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(8, 8), facecolor='w')
for param, unit, outlier_perc, ax, obs_df in zip(param_codes, units, outliers, axes.flatten(), obs_dfs):
	obs_df['year'] = pd.to_datetime(obs_df['obs_date'], errors='coerce').dt.year
	len_before = len(obs_df)
	min_year = obs_df['year'].min()
	max_year = 1970
	obs_df.drop(obs_df[obs_df['year'] < max_year].index, inplace=True)
	len_after = len(obs_df)
	before_perc = round((len_before - len_after) / len_before * 100, 1)
	if before_perc != 0.0:
		text = 'Percentage of observations {:.0f} - {:.0f}: {:.1f}%'.format(min_year, max_year, before_perc)
		ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=8)
		title_pad = 20
	ax.set_title(param, fontweight='bold', fontname='Arial', pad=title_pad, fontsize=10)
	for source, data in obs_df.groupby('source'):
		sns.histplot(
			ax=ax, data=data, x='year', hue='source', palette=color_dict, element='step',
			binwidth=1, stat='count'
		)
	ax.set_xlabel('year', fontname='Arial', fontsize=8)
	ax.set_ylabel('count', fontname='Arial', fontsize=8)
	ax.tick_params(labelsize=8)
	ax.legend([], [], frameon=False)
	ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
	ax.yaxis.offsetText.set_fontsize(8)
fig.tight_layout(h_pad=2)
fig.subplots_adjust(bottom=0.2)
legend_dict = collections.OrderedDict([])
for source, color in zip(sources, colors):
	legend_dict.update({source: color})
patches = []
for source in legend_dict:
	data_key = mpatches.Patch(color=legend_dict[source], label=source)
	patches.append(data_key)
fig.legend(handles=patches, loc='lower center', ncol=5, bbox_to_anchor=[0.5, 0.1], frameon=False, fontsize=8)
plt.savefig(
    os.path.join(fig_dir, ds_name + '_temporal_hist_grid.png'), dpi=300, bbox_inches='tight'
)

# Create histogram
fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(8, 8), facecolor='w')
for param, unit, outlier_perc, ax, obs_df in zip(param_codes, units, outliers, axes.flatten(), obs_dfs):
	ax.set_title(param, fontweight='bold', fontname='Arial', pad=24, fontsize=10)
	if outlier_perc != 0.0:
		text = 'Outliers detected by the IQR test ({}%) '.format(outlier_perc) + '\n' + 'have been removed'
		ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=8)
	sns.histplot(
		ax=ax, data=obs_df[obs_df['obs_iqr_outlier'] == 'no'], x='obs_value', hue='source', multiple='stack', bins=30, 
		stat='count', palette=color_dict, linewidth=0.1
	)
	ax.set_xlabel('observation value ({})'.format(unit), fontname='Arial', fontsize=8)
	ax.set_ylabel('count', fontname='Arial', fontsize=8)
	ax.tick_params(labelsize=8)
	ax.legend([], [], frameon=False)
	ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
	ax.yaxis.offsetText.set_fontsize(8)
fig.tight_layout(h_pad=2)
fig.subplots_adjust(bottom=0.2)
legend_dict = collections.OrderedDict([])
for source, color in zip(sources, colors):
	legend_dict.update({source: color})
patches = []
for source in legend_dict:
	data_key = mpatches.Patch(color=legend_dict[source], label=source)
	patches.append(data_key)
fig.legend(handles=patches, loc='lower center', ncol=5, bbox_to_anchor=[0.5, 0.1], frameon=False, fontsize=8)
plt.savefig(
    os.path.join(fig_dir, ds_name + '_hist_grid.png'), dpi=300, bbox_inches='tight'
)

# Create box plot
fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(8, 8), facecolor='w')
for param, unit, outlier_perc, ax, obs_df in zip(param_codes, units, outliers, axes.flatten(), obs_dfs):
	ax.set_title(param, fontweight='bold', fontname='Arial', pad=24, fontsize=10)
	if outlier_perc != 0.0:
		text = 'Outliers detected by the IQR test ({}%) '.format(outlier_perc) + '\n' + 'have been removed'
		ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=8)
	sns.boxplot(
		ax=ax, data=obs_df[obs_df['obs_iqr_outlier'] == 'no'], x='source', y='obs_value', hue='source', dodge=False,
		palette=color_dict, fliersize=1, linewidth=0.5, saturation=0.5, width=0.5
	)
	ax.set_xlabel('source dataset', fontname='Arial', fontsize=8)
	ax.set_ylabel('observation value ({})'.format(unit), fontname='Arial', fontsize=8)
	ax.legend([], [], frameon=False)
	ax.tick_params(labelsize=6)
fig.tight_layout()
plt.savefig(
    os.path.join(fig_dir, ds_name + '_box_grid.png'), dpi=300, bbox_inches='tight'
)
