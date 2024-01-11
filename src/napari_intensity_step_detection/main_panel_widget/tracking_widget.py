from pathlib import Path
from napari.utils import progress
import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLabel, QTabWidget
from napari_intensity_step_detection.base.plots import Histogram
from .general_plot import GeneralPlot
from napari_intensity_step_detection.base.track import Track, pd_to_tracks, tracks_to_pd, tracks_to_napari_tracks, tracks_to_tracks_meta, filter_tracks_by_id, TrackMetaModel, TrackMetaProxyModel
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import TrackLabels as Labels
from napari_intensity_step_detection.base.sliders import HFilterSlider
from qtpy.QtCore import Signal, QItemSelectionModel, QModelIndex, Qt
from napari.utils import notifications
import warnings
from napari_intensity_step_detection.main_panel_widget.quick_analysis_widget import QuickAnalysisWidget


class TrackList(QWidget):
    selectionChanged = Signal(QModelIndex, QModelIndex)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.track_meta_table = QTableView()
        self.layout().addWidget(self.track_meta_table)
        self.track_meta_table.setSortingEnabled(True)

    def set_model(self, model):
        # self.track_meta_table.clear()
        self.track_meta_table.setModel(model)
        self.selection_model = QItemSelectionModel(model)
        self.track_meta_table.setSelectionModel(self.selection_model)
        self.selection_model.currentChanged.connect(self.selectionChanged)


class TrackFilterControls(QWidget):
    propertyUpdated = Signal(str, tuple)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
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
                self.controls[property].valueChangedTitled.connect(
                    self.propertyUpdated)
            self.controls[property].setRange(
                (self.database[property].min(), self.database[property].max()))
            self.controls[property].setValue(
                (self.database[property].min(), self.database[property].max()))


class TracksOverview(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.hitogram = GeneralPlot(title="Tracks Overview")
        self.layout().addWidget(self.hitogram)
        self.motility = GeneralPlot(title="Tracks Motility")
        self.layout().addWidget(self.motility)

    def set_data_source(self, source):
        self.dataframe = source
        self.create_histogram()
        self.create_motility()

    def create_histogram(self):
        self.hitogram.clear()
        data = {}
        properties = []

        for property in self.dataframe.columns:
            property = str(property).strip()
            if property == 'track_id':
                continue
            y = self.dataframe[property].to_numpy()
            y = y[~np.isnan(y)]
            _property = {
                'type': 'histogram',
                'y': y,
                'label': property,
            }
            # data[property] = self.dataframe[property].to_numpy()
            properties.append(_property)
        data = {
            'data': properties
        }
        self.hitogram.setData(data=data)
        self.hitogram.draw()

    def create_motility(self):
        self.motility.clear()
        all_alpha = self.dataframe['msd_fit_alpha'].to_numpy()
        all_alpha = all_alpha[~np.isnan(all_alpha)]
        data = {
            'x_label': 'α',
            'y_label': 'Number of Track Segments',
            'data': {
                'y': all_alpha,
                'type': 'histline'
            }
        }
        self.motility.setData(data=data)
        self.motility.draw()


def _get_shape_layer_data(shape_layer):
    if shape_layer is None:
        return None
    shape_layer_data = shape_layer.data[0] if isinstance(
        shape_layer.data, list) else shape_layer.data
    shape_layer_data = shape_layer_data[:, 1:3]
    top_left = shape_layer_data[0]
    bottom_right = shape_layer_data[2]
    return top_left, bottom_right


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
        self.sbDelta.setValue(5.2)
        self.sbMinLength.setValue(5)
        self.sbMinLength.setMinimum(5)
        self.cbStepDetection.setChecked(False)

        def ifStepDetection(checked):
            if checked == 1:
                self.sbMinLength.setMinimum(10)
                self.sbMinLength.setValue(10)
            else:
                self.sbMinLength.setMinimum(5)
                self.sbMinLength.setValue(5)
        self.cbStepDetection.toggled.connect(ifStepDetection)

        # meta table view
        self.meta_table = TrackList(self)

        self.base.napari_viewer.window.add_dock_widget(
            self.meta_table, name="Track Info", area="left")

        # setup tracking view
        self.trackingView.setLayout(QVBoxLayout())
        self.trackingView.layout().setContentsMargins(0, 0, 0, 0)
        self.trackingTabs = QTabWidget()
        self.trackingView.layout().addWidget(self.trackingTabs)

        # setup filter view
        self.filterOverView = QWidget()
        self.filterOverView.setLayout(QVBoxLayout())
        self.tracksOverview = TracksOverview()
        self.filterOverView.layout().addWidget(self.tracksOverview)

        # setup tracking controls
        self.controls = TrackFilterControls()
        self.filterOverView.layout().addWidget(self.controls)
        self.trackingTabs.addTab(self.filterOverView, "Filter")

        # setup quick analysis view
        self.quickAnalysisView = QuickAnalysisWidget(self.base)
        self.trackingTabs.addTab(self.quickAnalysisView, "Quick Analysis")

        def _start_tracking():
            if (not self.base.get_layer('Image')) and (not self.base.get_layer('Label')):
                warnings.warn("No Image or Lable selected!")
                notifications.show_warning("No Image or Lable selected!")
                return
            try:
                self.btnTrack.setEnabled(False)
                self.track()
            except Exception as e:
                notifications.show_error(str(e))
                raise e
            finally:
                self.btnTrack.setEnabled(True)

        self.btnTrack.clicked.connect(_start_tracking)

    def filter_tracks(self, property, vrange):
        current_track_layer = self.base.get_layer('Track')
        if current_track_layer is None:
            warnings.warn("No Track selected!")
            notifications.show_warning("No Track selected!")
            return
        all_tracks_meta = current_track_layer.metadata['all_meta']
        all_tracks = current_track_layer.metadata['all_tracks']

        filtered_tracks_meta = all_tracks_meta[all_tracks_meta[property].between(
            vrange[0], vrange[1])]
        filtered_track_ids = filtered_tracks_meta['track_id'].to_numpy()
        filtered_tracks = filter_tracks_by_id(all_tracks, filtered_track_ids)

        napari_tracks, properties = tracks_to_napari_tracks(filtered_tracks)
        filtered_tracks_meta = tracks_to_tracks_meta(filtered_tracks)

        utils.add_to_viewer(self.base.napari_viewer, current_track_layer.name, napari_tracks, "tracks",
                            properties=properties,
                            scale=current_track_layer.scale,
                            metadata={'all_meta': all_tracks_meta,
                                      'all_tracks': all_tracks,
                                      "filter_meta": filtered_tracks_meta,
                                      "filter_tracks": filtered_tracks,
                                      'tracking_params': current_track_layer.metadata['tracking_params']})
        self.tracksOverview.set_data_source(filtered_tracks_meta)

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
        bounds = _get_shape_layer_data(self.base.get_layer('Shape'))
        self.tracks = pd_to_tracks(tracked_df, is_3d=False,
                                   delta=self.sbDelta.value(), min_length=int(self.sbMinLength.value()), step_detection=self.cbStepDetection.isChecked(), ignore_reagion=bounds, progress=progress)
        tracks = self.tracks
        napari_tracks, properties = tracks_to_napari_tracks(
            tracks, progress=progress)
        track_meta = tracks_to_tracks_meta(tracks, progress=progress)

        pbr.update(100)
        pbr.close()
        # update napari viewer
        utils.add_to_viewer(self.base.napari_viewer, f"{image_layer.name} tracks", napari_tracks, "tracks",
                            properties=properties,
                            scale=image_layer.scale,
                            metadata={
                                'all_meta': track_meta,
                                'all_tracks': tracks,
                                'tracking_params': {
                                    "search_range": search_range,
                                    "memory": memory
                                }
                            }
                            )

        # update filter view
        self.tracksOverview.set_data_source(track_meta)
        self.controls.set_properties(track_meta)
        self.controls.propertyUpdated.connect(self.filter_tracks)

        # meta_models
        self.track_meta_model = TrackMetaModel(track_meta)
        self.track_meta_model_proxy = TrackMetaProxyModel()
        self.track_meta_model_proxy.setTrackMetaModel(self.track_meta_model)

        self.meta_table.set_model(self.track_meta_model_proxy)

        self.controls.propertyUpdated.connect(
            self.track_meta_model_proxy.property_filter_updated)

        self.meta_table.selectionChanged.connect(self.track_selection_changed)
        # tell everyone that new data is ready
        self.base.updated.emit()

    def track_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        current_track_layer = self.base.get_layer('Track')
        if current_track_layer is None:
            warnings.warn("No Track selected!")
            notifications.show_warning("No Track selected!")
            return
        track_id_index = self.track_meta_model_proxy.index(
            current.row(), 0, current.parent())
        track_id = self.track_meta_model_proxy.data(
            track_id_index, role=Qt.ItemDataRole.DisplayRole)

        track_id = int(float(track_id.strip()))

        track = filter_tracks_by_id(self.tracks, [track_id])[0]
        self.quickAnalysisView.set_traget_track(track)

        utils.add_to_viewer(self.base.napari_viewer, "Selected Track", track.napari_points, "tracks",
                            scale=current_track_layer.scale)
