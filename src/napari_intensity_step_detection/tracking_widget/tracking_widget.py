from pathlib import Path
import napari
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QVBoxLayout
from napari_intensity_step_detection.base_widgets.base_widget import NLayerWidget
from napari_intensity_step_detection.filter_widget.property_filter_widget import PropertyFilter
from qtpy import uic
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.base_widgets import AppState


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
        # tracking controls
        self.state = app_state
        self.filter_propery = 'length'
        self.ui = _tracking_ui(self)
        self.layout().addWidget(self.ui)
        # self.ui.filterView.setLayout(QVBoxLayout())
        # propertyFilter = PropertyFilter(napari_view=napari_viewer, parent=self, include_properties=['length'])
        # propertyFilter.gbNapariLayers.setVisible(False)
        # propertyFilter.ui.tabWidget.setVisible(False)
        # self.ui.filterView.layout().addWidget(propertyFilter)
        # self.ui.filterView.layout().setContentsMargins(0, 0, 0, 0)

        def _start_tracking():
            self.track()

        self.ui.btnTrack.clicked.connect(_start_tracking)

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

        pbr.update(100)
        pbr.close()

        tracks, properties, track_meta = utils.pd_to_napari_tracks(tracked_df,
                                                                   Labels.track_header,
                                                                   Labels.track_meta_header)

        self.state.setData("tracking_all_tracks", tracked_df)
        self.state.setData("tracking_all_meta", track_meta)

        _add_to_viewer(self.viewer, Labels.tracks_layer, tracks, properties=properties,
                       metadata={'all_meta': track_meta,
                                 'all_tracks': tracked_df,
                                 Labels.tracking_params: {
                                     "search_range": search_range,
                                     "memory": memory
                                 }
                                 })

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
