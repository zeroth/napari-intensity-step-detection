from pathlib import Path
from qtpy import uic
import pandas as pd
from napari_intensity_step_detection.base_widgets import NLayerWidget, TrackMetaModelProxy, TrackMetaModel, AppState
from napari_intensity_step_detection.base_widgets.sliders import HFilterSlider
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Signal
import napari


class PropertyFilter(QWidget):
    def __init__(self, app_state: AppState = None, include_properties=None, parent: QWidget = None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'filter_view.ui')
        self.load_ui(UI_FILE)
        self.state = app_state
        self.setup_ui()
        if include_properties is None:
            self.include_properties = []
        else:
            self.include_properties = include_properties

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setup_ui(self):
        if self.get_current_track_layer() is None:
            return

        track_layer = self.get_current_track_layer()
        track_meta = track_layer.metadata['all_meta']
        track_all_tracks = track_layer.metadata['all_tracks']
        self.model = TrackMetaModel(track_meta, self.track_id_column_name)
        self.all_tracks = track_all_tracks
        self.ui.allView.setModel(self.model)

        self.proxy_model = TrackMetaModelProxy()
        self.proxy_model.setTrackModel(self.model)
        self.ui.filterView.setModel(self.proxy_model)
        self.ui.filterPlots.include_properties = self.include_properties
        self.ui.filterPlots.setModel(self.proxy_model)
        self.add_controls(track_meta)
        self.propertyUpdated.connect(self.proxy_model.property_filter_updated)

        # # setup histogram
        # _properties = list(track_meta.columns)
        # _properties.remove(self.track_id_column_name)
        # self.ui.filterProperties.setItems(_properties)

        # def _filter_combo_chnaged():
        #     current_text = self.ui.filterProperties.currentText()
        #     print(current_text)

        # self.ui.filterProperties.currentTextChanged.connect(_filter_combo_chnaged)

    def add_controls(self, track_meta: pd.DataFrame):
        self.ui.filterControls.setLayout(QVBoxLayout())
        self.ui.filterControls.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.filterControls.layout().setSpacing(2)
        for p in track_meta.columns:
            if p == self.track_id_column_name:
                continue
            if (len(self.include_properties)) and (p not in self.include_properties):
                continue
            _slider = HFilterSlider()
            _slider.setTitle(p)
            _p_np = track_meta[p].to_numpy()
            _vrange = (_p_np.min(), _p_np.max())
            _slider.setRange(_vrange)
            _slider.setValue(_vrange)
            _slider.valueChangedTitled.connect(self.propertyUpdated)

            self.ui.filterControls.layout().addWidget(_slider)

    def get_current_track_layer(self):
        return self.get_layer("Tracks")

    def get_current_image_data(self):
        return None if self.get_current_track_layer() is None else self.get_current_track_layer().data


class PropertyFilterWidget(NLayerWidget):
    propertyUpdated = Signal(str, tuple)

    def __init__(self, app_state: AppState = None, parent: QWidget = None, include_properties=None):
        super().__init__(app_state=app_state, parent=parent)
        self.ui = PropertyFilter(self, app_state=self.state, include_properties=include_properties)
        self.layout().addWidget(self.ui)
        self.track_id_column_name = 'track_id'
        self.layer_filter = {"Tracks": napari.layers.Tracks}

        def _call_setup_ui(event):
            if isinstance(event.value, napari.layers.Tracks):
                self.setup_ui()

        self.layers_hooks.append(_call_setup_ui)

    # def setup_ui(self):
    #     if self.get_current_track_layer() is None:
    #         return

    #     track_layer = self.get_current_track_layer()
    #     track_meta = track_layer.metadata['all_meta']
    #     track_all_tracks = track_layer.metadata['all_tracks']
    #     self.model = TrackMetaModel(track_meta, self.track_id_column_name)
    #     self.all_tracks = track_all_tracks
    #     self.ui.allView.setModel(self.model)

    #     self.proxy_model = TrackMetaModelProxy()
    #     self.proxy_model.setTrackModel(self.model)
    #     self.ui.filterView.setModel(self.proxy_model)
    #     self.ui.filterPlots.include_properties = self.include_properties
    #     self.ui.filterPlots.setModel(self.proxy_model)
    #     self.add_controls(track_meta)
    #     self.propertyUpdated.connect(self.proxy_model.property_filter_updated)

    #     # # setup histogram
    #     # _properties = list(track_meta.columns)
    #     # _properties.remove(self.track_id_column_name)
    #     # self.ui.filterProperties.setItems(_properties)

    #     # def _filter_combo_chnaged():
    #     #     current_text = self.ui.filterProperties.currentText()
    #     #     print(current_text)

    #     # self.ui.filterProperties.currentTextChanged.connect(_filter_combo_chnaged)

    # def add_controls(self, track_meta: pd.DataFrame):
    #     self.ui.filterControls.setLayout(QVBoxLayout())
    #     self.ui.filterControls.layout().setContentsMargins(0, 0, 0, 0)
    #     self.ui.filterControls.layout().setSpacing(2)
    #     for p in track_meta.columns:
    #         if p == self.track_id_column_name:
    #             continue
    #         if (len(self.include_properties)) and (p not in self.include_properties):
    #             continue
    #         _slider = HFilterSlider()
    #         _slider.setTitle(p)
    #         _p_np = track_meta[p].to_numpy()
    #         _vrange = (_p_np.min(), _p_np.max())
    #         _slider.setRange(_vrange)
    #         _slider.setValue(_vrange)
    #         _slider.valueChangedTitled.connect(self.propertyUpdated)

    #         self.ui.filterControls.layout().addWidget(_slider)

    # def get_current_track_layer(self):
    #     return self.get_layer("Tracks")

    # def get_current_image_data(self):
    #     return None if self.get_current_track_layer() is None else self.get_current_track_layer().data
