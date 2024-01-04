from scipy.optimize import curve_fit
from math import sqrt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import warnings
# from warnings import RuntimeWarning
warnings.filterwarnings('ignore', category=RuntimeWarning)
# plt.rcParams['figure.figsize'] = [20, 20]
# "D:\EHD1 WT and T94A-20231223T060629Z-001\EHD1 WT and T94A\WT\12_25_2023_15_34_14"
data_path = os.path.join(
    "D:\\EHD1 WT and T94A-20231223T060629Z-001\\EHD1 WT and T94A\\WT", "12_25_2023_15_34_14")
track_meta_path = os.path.join(data_path, "track_meta.csv")
all_tracks_path = os.path.join(data_path, "all_tracks.csv")
msd_fit_alfa_path = os.path.join(data_path, "msd_fit_alfa.json")
lvi_path = os.path.join(data_path, "lifetime_vs_intensity.csv")
delta = 5.2

track_meta = pd.read_csv(track_meta_path)
all_tracks = pd.read_csv(all_tracks_path)
lvi = pd.read_csv(lvi_path)
with open(msd_fit_alfa_path, 'r') as f:
    msd_fit_alfa = json.loads(f.read())


def filter_tracks(pair):
    k, v = pair
    if v > 2:
        return True
    else:
        return False


fl = filter(filter_tracks, msd_fit_alfa.items())
msd_fit = dict(fl)


def msd_fit_function(delta, d, alfa):
    return (4*d) * np.power(delta, alfa)


def vector_distance(a, b):
    return abs(sqrt(((b[0] - a[0])**2) + ((b[1] - a[1])**2)))


def msd(pos, result_columns, pos_columns, limit=25):
    limit = min(limit, len(pos) - 1)
    lagtimes = np.arange(1, limit+1)
    msd_list = []
    for lt in lagtimes:
        diff = pos[lt:] - pos[:-lt]
        msd_list.append(np.concatenate((np.nanmean(diff, axis=0),
                                        np.nanmean(diff**2, axis=0))))
    result = pd.DataFrame(msd_list, columns=result_columns, index=lagtimes)
    result['msd'] = result[result_columns[-len(pos_columns):]].sum(1)
    return result


def basic_msd_fit(msd_y, limit=26, diff=vector_distance):
    y = np.array(msd_y)
    # x = np.array(list(range(1, len(y) + 1))) * 3.8
    x = np.array(list(range(1, len(y) + 1)))

    init = np.array([.001, .01])
    best_value, _ = curve_fit(msd_fit_function, x, y, p0=init, maxfev=10000)
    _y = msd_fit_function(x, best_value[0], best_value[1])

    return best_value[1], _y


# msd = {'type': 'msd', 'data': {
#             'x_label': 'delay', 'y_label': 'msd', 'series': []}}
msd_series = []

tg = all_tracks.groupby('track_id', as_index=False,
                        group_keys=True, dropna=True)
for name, group in tg:

    # if str(name) not in msd_fit:
    #     continue
    # print(str(name))
    # print("found")
    track = group[['x', 'y', 'intensity_mean', 'frame']].sort_values('frame')
    # print(track.shape)
    if track.shape[0] < 10:
        continue

    pos_columns = ['x', 'y']
    result_columns = ['<{}>'.format(p) for p in pos_columns] + \
        ['<{}^2>'.format(p) for p in pos_columns]

    pos = track.set_index('frame')[pos_columns]
    pos = pos.reindex(np.arange(pos.index[0], 1 + pos.index[-1]))
    result = msd(pos.values, result_columns=result_columns,
                 pos_columns=pos_columns, limit=26)

    y = result['msd'].to_numpy()

    alfa, _y = basic_msd_fit(y)
    if alfa > 3:
        print(f"alfa > 3 {name} {alfa}")
    # _x = np.arange(0, len(y)) * 3.8
    _x = np.arange(0, len(y))
    series = {
        'track_id': name,
        'msd': {'type': 'scatter', 'y': y, 'x': _x},
        'msf_fit': {'type': 'line', 'y': _y, 'x': _x},
        'alfa': alfa
    }
    msd_series.append(series)

figur_path = os.path.join(data_path, "figurs_overlay_v2")
os.makedirs(figur_path, exist_ok=True)


# # fig, axs = plt.subplots(nrows=18, ncols=2)
# for i in range(len(msd_series)):
#     s = msd_series[i]
#     f = plt.figure(i)
#     f.set_size_inches(18, 9)    
#     ax = f.subplots()        
#     ax.scatter(s['msd']['x'], s['msd']['y'], label=s['track_id'], marker='.', color='r')
#     ax.plot(s['msf_fit']['y'], label=s['track_id'], color='g')
#     ax.grid(True)
#     ax.set_ylabel('msd')
#     ax.set_xlabel('length')
#     f.suptitle(f"track_id: {s['track_id']} , alpha: {s['alfa']}")
#     f.savefig(os.path.join(
#         figur_path, f"overlay_track_id_{s['track_id']}_alpha_{s['alfa']}.png"))
#     f.show()

# plt.show()

# fig, axs = plt.subplots(nrows=18, ncols=2)
f = plt.figure(0)
f.set_size_inches(18, 9)    
ax = f.subplots()        

for i in range(len(msd_series)):
    s = msd_series[i]
    ax.scatter(s['msd']['x'], s['msd']['y'], label=s['track_id'], marker='.', color='r')
    ax.plot(s['msf_fit']['y'], label=s['track_id'], color='g')
    ax.grid(True)
    ax.set_ylabel('msd')
    ax.set_xlabel('length')
f.suptitle(f"msd alpha")
f.savefig(os.path.join(
    figur_path, f"overlay_track_id_alpha_{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.png"))
f.show()

plt.show()
