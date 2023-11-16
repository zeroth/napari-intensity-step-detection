from pathlib import Path
import napari
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import QItemSelectionModel
from napari_intensity_step_detection.base_widgets import (NLayerWidget, TrackMetaModelProxy,
                                                          TrackMetaModel, AppState)
from napari_intensity_step_detection.filter_widget.property_filter_widget import PropertyFilter
from qtpy import uic
from napari_intensity_step_detection import utils


class Labels:
    tracks_layer = "All Tracks"
    tracks_meta = "tracks_meta_data"
    tracking_params = "tracking_params"
    track_id = "track_id"
    track_header = ['track_id', 'frame', 'y', 'x']
    track_meta_header = ['track_id', 'length',
                         'intensity_max', 'intensity_mean', 'intensity_min']
    track_table_header = ['label', 'y', 'x', 'intensity_mean',
                          'intensity_max', 'intensity_min', 'area', 'frame', 'track_id']


class _tracking_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'tracking_widget.ui')
        self.load_ui(UI_FILE)
        self.sbSearchRange.setValue(2)
        self.sbMemory.setValue(1)

    def load_ui(self, path):
        uic.loadUi(path, self)


class TrackingWidget(NLayerWidget):

    def __init__(self, app_state: AppState = None, parent: QWidget = None):
        super().__init__(app_state, parent)
        self.name = "tracking"
        # tracking controls
        self.filter_propery = 'length'
        self.ui = _tracking_ui(self)
        self.layout().addWidget(self.ui)
        self.ui.filterView.setLayout(QVBoxLayout())
        propertyFilter = PropertyFilter(app_state=self.state, include_properties=['length'], parent=self)
        propertyFilter.tabWidget.setVisible(False)
        self.ui.filterView.layout().addWidget(propertyFilter)
        self.ui.filterView.layout().setContentsMargins(0, 0, 0, 0)

        def _start_tracking():
            self.track()

        self.ui.btnTrack.clicked.connect(_start_tracking)

        def _track_layer_added(event):
            if isinstance(event.value, napari.layers.Tracks):
                if hasattr(event.value, 'metadata') and ('all_meta' in event.value.metadata):
                    # self.setup_tracking(event.value)
                    layer = event.value
                    track_meta = layer.metadata['all_meta']
                    tracked_df = layer.metadata['all_tracks']
                    self.setup_tracking_state(tracked_df=tracked_df, track_meta=track_meta)

        self.state.nLayerInserted.connect(_track_layer_added)

        def _state_data_updated(key, val):
            if key == "tracking_df":
                dfs = self.state.data("tracking_df")
                all_meta = dfs['meta']
                self.setup_models(all_meta)

        self.state.dataUpdated.connect(_state_data_updated)

    def setup_tracking_state(self, tracked_df, track_meta):
        print("setup_tracking_state")
        self.state.setData(f"{self.name}_df", {"tracks": tracked_df, "meta": track_meta})
        self.setup_models(track_meta)

    def setup_models(self, track_meta):
        print("setup_models")
        model = TrackMetaModel(track_meta, 'track_id')
        proxy_model = TrackMetaModelProxy()
        proxy_model.setTrackModel(model)

        proxy_selection = QItemSelectionModel(proxy_model)
        model_selection = QItemSelectionModel(model)
        self.state.setObject(f"{self.name}_model", {"model": model,
                                                    "proxy": proxy_model,
                                                    "model_selection": model_selection,
                                                    "proxy_selection": proxy_selection})

    def track(self):
        image = self.get_layer('Image').data
        mask = self.get_layer('Label').data
        search_range = float(self.ui.sbSearchRange.value())
        memory = int(self.ui.sbMemory.value())
        pbr = progress(total=100, desc="Tracking")

        image_layer = image
        mask_layer = mask
        main_pd_frame = utils.get_statck_properties(
            masks=mask_layer, images=image_layer, show_progress=False)

        pbr.update(10)

        tracked_df = utils.get_tracks(
            main_pd_frame, search_range=search_range, memory=memory)
        # column name change from particle to track_id
        tracked_df.rename(columns={'particle': 'track_id'}, inplace=True)

        tracks, properties, track_meta = utils.pd_to_napari_tracks(tracked_df,
                                                                   Labels.track_header,
                                                                   Labels.track_meta_header)
        self.setup_tracking_state(tracked_df=tracked_df, track_meta=track_meta)

        _add_to_viewer(self.viewer, Labels.tracks_layer, tracks, properties=properties,
                       metadata={'all_meta': track_meta,
                                 'all_tracks': tracked_df,
                                 Labels.tracking_params: {
                                     "search_range": search_range,
                                     "memory": memory
                                 }
                                 })

        pbr.update(100)
        pbr.close()

# Comman functions


def _add_to_viewer(viewer, name, data, properties=None, scale=None, metadata=None):
    try:
        viewer.layers[name].data = data
        viewer.layers[name].visible = True

        if properties is not None:
            viewer.layers[name].properties = properties
        if metadata is not None:
            viewer.layers[name].metadata = metadata
    except KeyError:
        viewer.add_tracks(data, name=name, properties=properties,
                          scale=scale, metadata=metadata)


def _napari_main():
    import napari
    viewer = napari.Viewer()
    win = TrackingWidget(viewer)
    viewer.window.add_dock_widget(win, name="Tracking", area="right")
    napari.run()


def _qt_main():
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = TrackingWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _napari_main()
