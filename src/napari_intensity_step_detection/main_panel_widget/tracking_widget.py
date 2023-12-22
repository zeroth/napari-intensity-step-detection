from pathlib import Path
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QVBoxLayout
from napari_intensity_step_detection.base.plots import Histogram
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import TrackLabels as Labels
from napari_intensity_step_detection.base.sliders import HFilterSlider
from qtpy.QtCore import Signal
from napari.utils import notifications
import warnings


class TrackFilterControls(QWidget):
    propertyUpdated = Signal(str, tuple)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.controls = {}

    def set_properties(self, dataframe):
        self.database = dataframe
        self.properties = dataframe.columns
        self.create_controls()

    def create_controls(self):
        for property in self.properties:
            property = str(property).strip()
            if property == 'track_id':
                continue
            if property not in self.controls:
                self.controls[property] = HFilterSlider(property)
                self.layout().addWidget(self.controls[property])
                self.controls[property].valueChangedTitled.connect(self.propertyUpdated)
            self.controls[property].setRange((self.database[property].min(), self.database[property].max()))
            self.controls[property].setValue((self.database[property].min(), self.database[property].max()))


class TrackFilter(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.plot = Histogram()
        self.layout().addWidget(self.plot)

    def set_data_source(self, source):
        self.dataframe = source
        self.draw()

    def draw(self):
        self.plot.clear()
        data = {}
        for property in self.dataframe.columns:
            property = str(property).strip()
            if property == 'track_id':
                continue
            data[property] = self.dataframe[property].to_numpy()
        self.plot.setData(data=data, title="Filtered View")
        self.plot.draw()


class Tracking(QWidget):

    def __init__(self, base, parent: QWidget = None):
        super().__init__(parent)
        self.name = "tracking"
        UI_FILE = Path(__file__).resolve().parent.joinpath(
            'tracking_widget.ui')
        utils.load_ui(UI_FILE, self)
        self.base = base

        self.sbSearchRange.setValue(2)
        self.sbMemory.setValue(1)

        # setup filter view
        self.trackFilter = TrackFilter()
        self.filterView.setLayout(QVBoxLayout())
        self.filterView.layout().addWidget(self.trackFilter)

        # setup tracking controls
        self.controls = TrackFilterControls()
        self.filterView.layout().addWidget(self.controls)

        def _start_tracking():
            if (not self.base.get_layer('Image')) and (not self.base.get_layer('Label')):
                warnings.warn("No Image or Lable selected!")
                notifications.show_warning("No Image or Lable selected!")
                return
            self.track()

        self.btnTrack.clicked.connect(_start_tracking)

    def filter_tracks(self, property, vrange):
        current_track_layer = self.base.get_layer('Track')
        if current_track_layer is None:
            warnings.warn("No Track selected!")
            notifications.show_warning("No Track selected!")
            return
        track_meta = current_track_layer.metadata['all_meta']

        track_meta_filtered = track_meta[track_meta[property].between(vrange[0], vrange[1])]
        track_ids = track_meta_filtered['track_id'].to_numpy()
        all_tracks = current_track_layer.metadata['all_tracks']
        filtered_tracks_df = all_tracks[all_tracks['track_id'].isin(track_ids)]

        filtered_tracks, properties, _ = utils.pd_to_napari_tracks(filtered_tracks_df,
                                                                   Labels.track_header,
                                                                   Labels.track_meta_header)

        utils.add_to_viewer(self.base.napari_viewer, current_track_layer.name, filtered_tracks, "tracks",
                            properties=properties, scale=current_track_layer.scale,
                            metadata={'all_meta': track_meta,
                                      'all_tracks': all_tracks,
                                      "filter_meta": track_meta_filtered,
                                      "filter_tracks": filtered_tracks_df,
                                      'tracking_params': current_track_layer.metadata['tracking_params']})
        self.trackFilter.set_data_source(track_meta_filtered)

    def track(self):
        image_layer = self.base.get_layer('Image')
        image = image_layer.data
        mask = self.base.get_layer('Label').data
        search_range = float(self.sbSearchRange.value())
        memory = int(self.sbMemory.value())
        pbr = progress(total=100, desc="Tracking")

        main_pd_frame = utils.get_statck_properties(
            masks=mask, images=image, show_progress=False)

        pbr.update(10)

        tracked_df = utils.get_tracks(main_pd_frame, search_range=search_range, memory=memory)
        # column name change from particle to track_id
        tracked_df.rename(columns={'particle': 'track_id'}, inplace=True)

        tracks, properties, track_meta = utils.pd_to_napari_tracks(tracked_df,
                                                                   Labels.track_header,
                                                                   Labels.track_meta_header)
        # self.setup_tracking_state(tracked_df=tracked_df, track_meta=track_meta)
        # self.state.setData(f"{self.name}", {"tracks_df": tracked_df, "meta_df": track_meta})

        pbr.update(100)
        pbr.close()

        utils.add_to_viewer(self.base.napari_viewer, f"{image_layer.name} tracks", tracks, "tracks",
                            properties=properties,
                            scale=image_layer.scale,
                            metadata={
                                        'all_meta': track_meta,
                                        'all_tracks': tracked_df,
                                        'tracking_params': {
                                            "search_range": search_range,
                                            "memory": memory
                                        }
                                      }
                            )

        # tell everyone that new data is ready
        self.base.updated.emit()

        # update filter view
        self.trackFilter.set_data_source(track_meta)
        self.controls.set_properties(track_meta)
        self.controls.propertyUpdated.connect(self.filter_tracks)
