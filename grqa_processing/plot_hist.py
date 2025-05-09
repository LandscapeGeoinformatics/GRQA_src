# Import the libraries
import sys
import os
import collections

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches

# Name of the dataset
ds_name = 'GRQA'

# Source dataset names
sources = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']

# Project directory
proj_dir = sys.argv[1]

# Get parameter code
param_code = sys.argv[2]

# Data directory
data_dir  = os.path.join(proj_dir, 'final', 'GRQA_data')

# Figure directory
fig_dir  = os.path.join(proj_dir, 'final', 'GRQA_figures')

# Import observation data
obs_dtypes = {
    'obs_id': object,
    'site_id': object,
    'obs_date': object,
    'obs_value': np.float64,
    'unit': object,
    'obs_iqr_outlier': object,
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

# Color dictionary
sources = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']
colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
color_dict = dict(zip(sources, colors))

# Create temporal distribution plot
obs_df['year'] = pd.to_datetime(obs_df['obs_date'], errors='coerce').dt.year
len_before = len(obs_df)
min_year = obs_df['year'].min()
xlim_start = 1970
max_year = obs_df['year'].max()
obs_df.drop(obs_df[obs_df['year'] < xlim_start].index, inplace=True)
len_after = len(obs_df)
before_perc = round((len_before - len_after) / len_before * 100, 1)
grouped = obs_df.groupby(['source', 'year'])['obs_value'].count().reset_index()
fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 4), facecolor='w')
title_pad = 5
if before_perc != 0.0:
    text = (
        'Percentage of observations {:.0f} - {:.0f}: {:.1f}%'
        .format(min_year, xlim_start, before_perc)
    )
    ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=6)
    title_pad = 20
ax.set_title(
    (
        'Temporal distribution of {} observation values {} - {}'
        .format(param_code, xlim_start, max_year)
    ), fontweight='bold',
    fontname='Arial', fontsize=8, pad=title_pad
)
for source, data in grouped.groupby('source'):
    sns.lineplot(ax=ax, data=data, x='year', y='obs_value', hue='source', palette=color_dict)
ax.set_xlabel('year', fontname='Arial')
ax.set_ylabel('observation count', fontname='Arial')
ax.legend([], [], frameon=False)
legend_dict = collections.OrderedDict([])
for source in sources:
    if source in obs_df['source'].unique():
        color = colors[sources.index(source)]
        legend_dict.update({source: color})
patches = []
for source in legend_dict:
    data_key = mpatches.Patch(color=legend_dict[source], label=source)
    patches.append(data_key)
fig.legend(
    handles=patches, loc='upper right', fontsize=8, bbox_to_anchor=[1.2, 0.8]
)
fig.tight_layout()
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_temporal_hist.png'), dpi=300, bbox_inches='tight'
)

# Drop outliers for histogram and box plot
obs_df.drop(obs_df[obs_df['obs_iqr_outlier'] == 'yes'].index, inplace=True)

# Create histogram
fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 4), facecolor='w')
title_pad = 0
if outlier_perc != 0.0:
    text = 'Outliers detected by the IQR test ({}% of observations) have been removed'.format(outlier_perc)
    ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=6)
    title_pad = 20
ax.set_title(
    'Histogram plot of ' + param_code + ' observation values', fontweight='bold', fontname='Arial', fontsize=8,
    pad=title_pad
)
sns.histplot(
    data=obs_df[obs_df['obs_iqr_outlier'] == 'no'], x='obs_value', hue='source', multiple='stack', bins=30,
    stat='count', palette=color_dict, linewidth=0.1, legend=True
)
ax.set_xlabel('observation value ({})'.format(unit), fontname='Arial')
ax.set_ylabel('count', fontname='Arial')
fig.tight_layout()
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_hist.png'), dpi=300, bbox_inches='tight', pad_inches=0
)

# Create box plot
fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 4), facecolor='w')
title_pad = 0
if outlier_perc != 0.0:
    text = 'Outliers detected by the IQR test ({}% of observations) have been removed'.format(outlier_perc)
    ax.text(0.5, 1.05, text, ha='center', va='center', transform=ax.transAxes, fontsize=6)
    title_pad = 20
ax.set_title(
    'Violin plot of ' + param_code + ' observation values', fontweight='bold', fontname='Arial', fontsize=8,
    pad=title_pad
)
sns.boxplot(
    ax=ax, data=obs_df[obs_df['obs_iqr_outlier'] == 'no'], x='source', y='obs_value', hue='source', dodge=False,
    palette=color_dict, fliersize=1, linewidth=0.5, saturation=0.5, width=0.5
)
ax.set_xlabel('source dataset', fontname='Arial')
ax.set_ylabel('observation value ({})'.format(unit), fontname='Arial')
ax.legend([], [], frameon=False)
fig.tight_layout()
plt.savefig(
    os.path.join(fig_dir, param_code + '_' + ds_name + '_box.png'), dpi=300, bbox_inches='tight'
)
