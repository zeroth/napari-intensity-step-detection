from napari_intensity_step_detection.base.widget import NLayerWidget
from qtpy.QtWidgets import QWidget, QPushButton, QTabWidget
import napari
from napari.utils import notifications
import warnings
from napari_intensity_step_detection import utils
import numpy as np
from .tracking_plots import TrackAnalysisResult
from collections import OrderedDict
import os
import sys
from datetime import datetime
import pandas as pd
import json


class TrackAnalysis(NLayerWidget):
    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer, parent)

        # set layer filter
        self.layer_filter = {"Track": napari.layers.Tracks,
                             "Shape": napari.layers.Shapes}
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze)
        self.actionArea.layout().addWidget(self.analyze_button)

        self.result_tabs = QTabWidget()
        self.layout().addWidget(self.result_tabs)

    def save_pd(self, df, name):
        now = datetime.now()
        quick_save_path = os.path.join(".", now.strftime("%m_%d_%Y_%H_%M_%S"))
        os.makedirs(quick_save_path, exist_ok=True)
        path = os.path.join(quick_save_path, f"{name}.csv")
        df.to_csv(path)
        print(f"Saved {path}")

    def analyze(self):

        track_layer = self.get_layer('Track')
        if track_layer is None:
            warnings.warn("No Image or Lable selected!")
            notifications.show_warning("No Image or Lable selected!")
            return

        track_meta = track_layer.metadata['all_meta']
        all_tracks = track_layer.metadata['all_tracks']

        if 'filter_tracks' in track_layer.metadata:
            print("Using filtered tracks")
            track_meta = track_layer.metadata['filter_meta']
            all_tracks = track_layer.metadata['filter_tracks']

        result_dict = {}
        all_alfa = {}

        self.save_pd(track_meta, "track_meta")
        self.save_pd(all_tracks, "all_tracks")

        def _get_shape_layer_data(shape_layer):
            if shape_layer is None:
                return None
            shape_layer_data = shape_layer.data[0] if isinstance(
                shape_layer.data, list) else shape_layer.data
            shape_layer_data = shape_layer_data[:, 1:3]
            top_left = shape_layer_data[0]
            bottom_right = shape_layer_data[2]
            return top_left, bottom_right

        def _is_track_in_box(point, top_left, bottom_right):
            return ((top_left[0] <= point[0] <= bottom_right[0])
                    or (top_left[0] >= point[0] >= bottom_right[0])) \
                and ((top_left[1] <= point[1] <= bottom_right[1])
                     or (top_left[1] >= point[1] >= bottom_right[1]))

        # track length
        result_dict['lifetime_histogram'] = {
            'x_label': 'track lifetime',
            'y_label': 'number of tracks',
            'data': {
                'type': 'histogram',
                'y': track_meta['length'].to_numpy(),
            },
        }
        # /track length

        # lifetime vs intensity
        lifetime_vs_intensity = {
            'type': 'scatter',
            'x': [],
            'y': [],

        }

        for index, row in track_meta.iterrows():
            lifetime_vs_intensity['x'].append(row['length'])
            lifetime_vs_intensity['y'].append(row['intensity_mean'])

        result_dict["lifetime_vs_intensity"] = {
            'x_label': 'track lifetime',
            'y_label': 'intensity',
            'data': lifetime_vs_intensity
        }

        # save lifetime vs intensity

        # self.save_pd(pd.DataFrame(lifetime_vs_intensity),
        #              "lifetime_vs_intensity")
        # /lifetime vs intensity

        # msd

        msd_data = []
        tg = all_tracks.groupby(
            'track_id', as_index=False, group_keys=True, dropna=True)
        for name, group in tg:
            track = group[['x', 'y', 'intensity_mean', 'frame']
                          ].sort_values('frame')
            _track = track.to_numpy()

            # filter track
            bounds = _get_shape_layer_data(self.get_layer('Shape'))
            if bounds is not None:
                if not _is_track_in_box(_track[0], bounds[0], bounds[1]):
                    continue
            # /filter track

            pos = track.set_index('frame')[['x', 'y']]
            pos = pos.reindex(np.arange(pos.index[0], 1 + pos.index[-1]))
            result = utils.msd(pos.values, limit=26)

            y = result.to_numpy()
            x = np.arange(0, len(y)) * 5.2
            alfa, _y = utils.basic_msd_fit(y, delta=5.2)
            all_alfa[name] = alfa
            if alfa > 2.0:
                print(f"Track {name} alfa {alfa}")

            msd_data.append({
                'type': 'scatter',
                'y': y, 'x': x
            })
            msd_data.append({
                'type': 'line',
                'y': _y,
                'x': x
            })

        result_dict["msd"] = {
            'x_label': 'delay',
            'y_label': 'msd',
            'data': msd_data
        }
        # save msd
        # pd.DataFrame(msd).to_csv(os.path.join(quick_save_path, "msd.csv"))
        # /msd

        # msd fit alfa
        print("msd fit alfa")
        # save msd fit alfa
        # pd.DataFrame(all_alfa).to_csv(os.path.join(
        #     quick_save_path, "msd_fit_alfa.csv"))
        # with open(os.path.join(quick_save_path, "msd_fit_alfa.json"), 'w') as f:
        #     f.write(json.dumps(all_alfa))

        all_alfa_vals = np.array(list(all_alfa.values()))

        result_dict["msd_fit_alfa"] = {
            'x_label': 'alfa',
            'y_label': 'number of tracks',
            'data': {
                'type': 'histline',
                'y': all_alfa_vals
                # 'range': [np.min(msd_plt_x), 0.4, 1.2,  np.max(msd_plt_x)],
            }
        }
        # /msd fit alfa

        result_widget = TrackAnalysisResult()
        result_widget.set_title(track_layer.name)
        result_widget.set_result_dict(result_dict)
        result_widget.draw()
        self.result_tabs.addTab(result_widget, f"Results {track_layer.name}")

# class TrackAnalysis(NLayerWidget):
#     def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
#         super().__init__(napari_viewer, parent)

#         # set layer filter
#         self.layer_filter = {"Track": napari.layers.Tracks,
#                              "Shape": napari.layers.Shapes}
#         self.analyze_button = QPushButton("Analyze")
#         self.analyze_button.clicked.connect(self.analyze)
#         self.actionArea.layout().addWidget(self.analyze_button)

#         self.result_tabs = QTabWidget()
#         self.layout().addWidget(self.result_tabs)

#     def analyze(self):
#         now = datetime.now()
#         quick_save_path = os.path.join(".", now.strftime("%m_%d_%Y_%H_%M_%S"))
#         os.makedirs(quick_save_path, exist_ok=True)

#         track_layer = self.get_layer('Track')
#         if track_layer is None:
#             warnings.warn("No Image or Lable selected!")
#             notifications.show_warning("No Image or Lable selected!")
#             return

#         track_meta = track_layer.metadata['all_meta']
#         all_tracks = track_layer.metadata['all_tracks']

#         if 'filter_tracks' in track_layer.metadata:
#             print("Using filtered tracks")
#             track_meta = track_layer.metadata['filter_meta']
#             all_tracks = track_layer.metadata['filter_tracks']

#         result_dict = {}
#         all_alfa = {}

#         # save track_meta and tracks
#         track_meta.to_csv(os.path.join(quick_save_path, "track_meta.csv"))
#         all_tracks.to_csv(os.path.join(quick_save_path, "all_tracks.csv"))

#         def _get_shape_layer_data(shape_layer):
#             if shape_layer is None:
#                 return None
#             shape_layer_data = shape_layer.data[0] if isinstance(
#                 shape_layer.data, list) else shape_layer.data
#             shape_layer_data = shape_layer_data[:, 1:3]
#             top_left = shape_layer_data[0]
#             bottom_right = shape_layer_data[2]
#             return top_left, bottom_right

#         def _is_track_in_box(point, top_left, bottom_right):
#             return ((top_left[0] <= point[0] <= bottom_right[0])
#                     or (top_left[0] >= point[0] >= bottom_right[0])) \
#                 and ((top_left[1] <= point[1] <= bottom_right[1])
#                      or (top_left[1] >= point[1] >= bottom_right[1]))

#         # track length
#         result_dict[track_layer.name] = {
#             'lifetime_histogram': {
#                 'type': 'histogram',
#                 'data': {
#                     'y': track_meta['length'].to_numpy(),
#                     'x_label': 'track lifetime',
#                     'y_label': 'number of tracks'
#                 },

#             }
#         }
#         # /track length

#         # lifetime vs intensity
#         lifetime_vs_intensity = {
#             'type': 'scatter',
#             'x': [],
#             'y': [],
#             'x_label': 'track lifetime',
#             'y_label': 'intensity'

#         }

#         for index, row in track_meta.iterrows():
#             lifetime_vs_intensity['x'].append(row['length'])
#             lifetime_vs_intensity['y'].append(row['intensity_mean'])

#         result_dict[track_layer.name]["lifetime_vs_intensity"] = {
#             'type': 'lifetime_vs_intensity',
#             'data': lifetime_vs_intensity
#         }

#         # save lifetime vs intensity
#         pd.DataFrame(lifetime_vs_intensity).to_csv(os.path.join(
#             quick_save_path, "lifetime_vs_intensity.csv"))
#         # /lifetime vs intensity

#         """
#         MsdPlot  dict_keys(['type', 'x', 'y'])
#         plot_axis  dict_keys(['type', 'x', 'y'])
#         MsdPlot  dict_keys(['x_label', 'y_label', 'series'])
#         plot_axis  dict_keys(['type', 'y'])
#         """
#         # msd
#         msd = {'type': 'msd', 'data': {
#             'x_label': 'delay', 'y_label': 'msd', 'series': []}}

#         tg = all_tracks.groupby(
#             'track_id', as_index=False, group_keys=True, dropna=True)
#         for name, group in tg:
#             track = group[['x', 'y', 'intensity_mean', 'frame']
#                           ].sort_values('frame')
#             _track = track.to_numpy()

#             # filter track
#             bounds = _get_shape_layer_data(self.get_layer('Shape'))
#             if bounds is not None:
#                 if not _is_track_in_box(_track[0], bounds[0], bounds[1]):
#                     continue
#             # /filter track

#             pos_columns = ['x', 'y']
#             result_columns = ['<{}>'.format(p) for p in pos_columns] + \
#                 ['<{}^2>'.format(p) for p in pos_columns]

#             pos = track.set_index('frame')[pos_columns]
#             pos = pos.reindex(np.arange(pos.index[0], 1 + pos.index[-1]))
#             result = utils.msd(
#                 pos.values, result_columns=result_columns, pos_columns=pos_columns, limit=26)

#             y = result['msd'].to_numpy()

#             alfa, _y = utils.basic_msd_fit(y)
#             all_alfa[name] = alfa

#             series = {
#                 'track_id': name,
#                 'msd': {'type': 'scatter', 'y': y, 'x': np.arange(0, len(y))},
#                 'msf_fit': {'type': 'line', 'y': _y},
#                 'alfa': alfa
#             }
#             msd['data']['series'].append(series)

#         result_dict[track_layer.name]["msd"] = msd
#         # save msd
#         # pd.DataFrame(msd).to_csv(os.path.join(quick_save_path, "msd.csv"))
#         # /msd

#         # msd fit alfa
#         print("msd fit alfa")
#         # save msd fit alfa
#         # pd.DataFrame(all_alfa).to_csv(os.path.join(
#         #     quick_save_path, "msd_fit_alfa.csv"))
#         with open(os.path.join(quick_save_path, "msd_fit_alfa.json"), 'w') as f:
#             f.write(json.dumps(all_alfa))

#         all_alfa_vals = np.array(list(all_alfa.values()))
#         # msd_plt_y, msd_plt_x = utils.msd_alfa_plot(all_alfa_vals)
#         result_dict[track_layer.name]["msd_fit_alfa"] = {
#             'type': 'msd_fit_alfa',
#             'data': {
#                 'type': 'line',
#                 'y': all_alfa_vals,
#                 # 'range': [np.min(msd_plt_x), 0.4, 1.2,  np.max(msd_plt_x)],
#                 'x_label': 'alfa',
#                 'y_label': 'number of tracks'
#             }
#         }
#         # /msd fit alfa

#         result_widget = TrackAnalysisResult()
#         result_widget.set_title(track_layer.name)
#         result_widget.set_result_dict(result_dict)
#         result_widget.draw()
#         self.result_tabs.addTab(result_widget, f"Results {track_layer.name}")


"""
result_dict = {
    'plot_category': {
        'data':[{
            'type': 'scatter',
            'x': [],
            'y': [],
            'x_label': 'x values',
            'y_label': 'y values'

        },
        {
            'type': 'line',
            'x': [],
            'y': [],
            'x_label': 'x values',
            'y_label': 'y values'

        },
        {
            'type': 'histogram',
            'x': [], # bin edges
            'y': [], # bin counts/ histogram
            'x_label': 'x values',
            'y_label': 'y values'

        },
        ],

        },
        'plot_category2': {
        'data':[{
            'type': 'scatter',
            'x': [],
            'y': [],
            'x_label': 'x values',
            'y_label': 'y values'

        },
        {
            'type': 'line',
            'x': [],
            'y': [],
            'x_label': 'x values',
            'y_label': 'y values'

        },
        {
            'type': 'histogram',
            'x': [], # bin edges
            'y': [], # bin counts/ histogram
            'x_label': 'x values',
            'y_label': 'y values'

        },
        ],

        },
}
"""
