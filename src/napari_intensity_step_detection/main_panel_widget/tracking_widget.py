from pathlib import Path
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QVBoxLayout
from napari_intensity_step_detection.base.plots import Histogram
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import TrackLabels as Labels


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

        def _start_tracking():
            self.track()

        self.btnTrack.clicked.connect(_start_tracking)

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

        tracked_df = utils.get_tracks(
            main_pd_frame, search_range=search_range, memory=memory)
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
                            metadata={'all_meta': track_meta,
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
