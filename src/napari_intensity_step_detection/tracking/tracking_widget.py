import os
import sys
from pathlib import Path
import typing
import copy

import numpy as np
import napari
from napari.utils import progress

from qtpy.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget, QListWidget, QListWidgetItem, QSpinBox, QDoubleSpinBox, QFileDialog, QMessageBox
from superqt import QLabeledSlider as QSlider
from qtpy.QtGui import QStandardItemModel
from qtpy.QtCore import Signal, QItemSelectionModel, QModelIndex, Qt
from ..base.base_widget import NLayerWidget

import pandas as pd


class TrackingWidget(NLayerWidget):
    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer, parent)

        # members
        self.filtered_track_layer:napari.layers.Tracks = None
        self.selected_track_layer:napari.layers.Tracks = None
        self.tracks = np.zeros([1])
        self.steps_info = pd.DataFrame()
        self.selected_track_id = -1
        #/ members

        sb_search_range = QDoubleSpinBox()
        sb_search_range.setMinimum(1.0)
        sb_search_range.setValue(2.0)
        sb_memory = QSpinBox()
        sb_memory.setMinimum(0)
        sb_memory.setValue(1)
        btn_track = QPushButton("Track")
        
        def _track():
            self.track(
                self.get_layer('Image').data,
                self.get_layer('Label').data,
                search_range=float(sb_search_range.value()),
                memory=int(sb_memory.value())
            )
        btn_track.clicked.connect(_track)

        layer_layout = QFormLayout()
        layer_layout.addRow("Search Range", sb_search_range)
        layer_layout.addRow("Memory", sb_memory)
        self.layout().addLayout(layer_layout)
        self.layout().addWidget(btn_track)


    def pd_to_napari_tracks(self, df):
        # assuming df is the dataframe with 'particle' as track_id
        dataframe = df
        tracks = []
        properties = {}
        track_header = ['track_id', 'frame', 'y', 'x']
        track_meta_header = ['track_id', 'length', 'intensity_max', 'intensity_mean', 'intensity_min']
        columns = list(df.columns)

        for th in track_header:
            columns.remove(th)
        
        tg = df.groupby('track_id', as_index=False, group_keys=True, dropna=True)
        table = []
        for track_id, group in tg:
            row = [int(track_id), len(group), group['intensity_mean'].max(), group['intensity_mean'].mean(), group['intensity_mean'].min()]
            table.append(row)
        
        track_meta = pd.DataFrame(table, columns=track_meta_header)

        for c in columns:
            properties[c] = df[c].to_numpy()

        tracks = df[track_header].to_numpy()

        return tracks, properties, track_meta

    def track(self, image, mask, search_range, memory):
        from particle_tracking.utils import get_statck_properties, get_tracks
        pbr = progress(total=100, desc="Tracking")
        
        image_layer = image
        mask_layer = mask
        main_pd_frame = get_statck_properties(masks=mask_layer, images=image_layer, show_progress=False)

        pbr.update(10)
        
        tracked = get_tracks(main_pd_frame, search_range=search_range, memory=memory)
        tracked.rename(columns={'particle':'track_id'}, inplace=True) # column name change from particle to track_id 
        
        pbr.update(100)
        pbr.close()
        
        self.pd_to_tracks(tracked)

    def pd_to_tracks(self, tracks_df):
        self.all_tracks = tracks_df

        tracks, properties, track_meta = self.pd_to_napari_tracks(df=tracks_df)

        self.all_track_meta = track_meta

        _add_to_viewer(self.viewer, "All Tracks", tracks, properties=properties, metadata=track_meta.to_dict())

        
def _add_to_viewer(viewer, name, data, properties=None, scale=None, metadata=None):
    try:
        viewer.layers[name].data = data
        viewer.layers[name].visible = True
        viewer.layers[name].properties = properties
    except KeyError:
            viewer.add_tracks(data, name=name, properties=properties, scale=scale, metadata=metadata)