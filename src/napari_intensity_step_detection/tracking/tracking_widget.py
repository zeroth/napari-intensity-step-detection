from pathlib import Path
import napari
from napari.utils import progress
from qtpy.QtWidgets import QWidget
from napari_intensity_step_detection.base.base_widget import NLayerWidget
import pandas as pd
import warnings
# from napari_intensity_step_detection.base.plots import HistogramWidget
from qtpy import uic
import numpy as np


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
        self.slFilter.setTracking(False)

    def load_ui(self, path):
        uic.loadUi(path, self)


class TrackingWidget(NLayerWidget):

    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer, parent)
        # tracking controls
        self.ui = _tracking_ui(self)
        self.layout().addWidget(self.ui)

        def _track():
            self.track(
                self.get_layer('Image').data,
                self.get_layer('Label').data,
                search_range=float(self.ui.sbSearchRange.value()),
                memory=int(self.ui.sbMemory.value())
            )
            self.ui.grFilter.setVisible(True)
            self.init_filter()

        self.ui.btnTrack.clicked.connect(_track)
        self.ui.grFilter.setVisible(False)

    def add_filter(self):
        filter_range = self.ui.slFilter.value()
        filter_property = self.ui.cbProperties.currentText()
        # self.ui.filterList.addItem()

    def apply_filter(self, vrange, property, meta, tracks):
        vmin, vmax = vrange
        filter_txt = property
        filtered_meta = meta[(meta[filter_txt] >= vmin) &
                             (meta[filter_txt] <= vmax)]
        filtered_track_ids = filtered_meta['track_id']
        filtered_tracks = tracks.loc[tracks['track_id'].isin(
            filtered_track_ids)]
        return filtered_tracks

    def track(self, image, mask, search_range, memory):
        from particle_tracking import utils
        pbr = progress(total=100, desc="Tracking")

        image_layer = image
        mask_layer = mask
        main_pd_frame = utils.get_statck_properties(
            masks=mask_layer, images=image_layer, show_progress=False)

        pbr.update(10)

        tracked = utils.get_tracks(
            main_pd_frame, search_range=search_range, memory=memory)
        # column name change from particle to track_id
        tracked.rename(columns={'particle': 'track_id'}, inplace=True)

        pbr.update(100)
        pbr.close()

        self.create_all_tracks(tracked, search_range, memory)

    def create_all_tracks(self, tracks_df, search_range, memory):
        tracks, properties, track_meta = pd_to_napari_tracks(df=tracks_df)
        # initial tracking results
        self.all_tracks = tracks
        self.all_tracks_properties = properties
        self.all_tracks_df = tracks_df
        self.all_tracks_meta = track_meta

        self.d_all_tracks = tracks
        self.d_all_tracks_properties = properties
        self.d_all_tracks_df = tracks_df
        self.d_all_tracks_meta = track_meta

        _add_to_viewer(self.viewer, Labels.tracks_layer, tracks, properties=properties,
                       metadata={Labels.tracks_meta: track_meta,
                                 Labels.tracking_params: {
                                     "search_range": search_range,
                                     "memory": memory
                                 }
                                 })

        # self.add_filter_widget(self.viewer.layers[Labels.tracks_layer])

    def reset_view(self):
        _add_to_viewer(self.viewer, Labels.tracks_layer, self.all_tracks, properties=self.all_tracks_properties,
                       metadata={Labels.tracks_meta: self.all_tracks_meta,
                                 Labels.tracking_params: {
                                     "search_range": self.ui.slFilter.value(),
                                     "memory": self.ui.sbMemory.value()
                                 }
                                 })

    def set_filter_range(self):
        property = self.ui.cbProperties.currentText()
        _lengthRange = self.all_tracks_meta[property].to_numpy()
        self.ui.slFilter.setRange((_lengthRange.min(), _lengthRange.max()))
        self.ui.slFilter.setValue((_lengthRange.min(), _lengthRange.max()))
        self.ui.flHistogram.draw(_lengthRange, property)

        def _apply_filter():
            # slot
            filtered_tracks = self.apply_filter(self.ui.slFilter.value(),
                                                self.ui.cbProperties.currentText(),
                                                self.all_tracks_meta, self.all_tracks_df)
            _tracks, _propeties, meta = pd_to_napari_tracks(filtered_tracks)
            # update track view
            _add_to_viewer(self.viewer, Labels.tracks_layer,
                           _tracks, _propeties)

            # update histogram
            self.ui.flHistogram.draw(meta[self.ui.cbProperties.currentText()].to_numpy(),
                                     self.ui.cbProperties.currentText())

        self.ui.slFilter.valueChanged.connect(_apply_filter)

    def init_filter(self):
        properties = list(filter(lambda x: x.strip() !=
                          'track_id', Labels.track_meta_header))
        self.ui.cbProperties.addItems(properties)
        self.ui.cbProperties.setCurrentText('length')
        self.set_filter_range()

        def _cbProperties_Text_Change():
            self.set_filter_range()
            self.reset_view()

        self.ui.cbProperties.currentTextChanged.connect(
            _cbProperties_Text_Change)

        self.ui.btnAddFilter.clicked.connect(self.add_filter)


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


def napari_track_to_pd(track_layer: napari.layers.Tracks):
    """
    This function converts the napari Tracks layer to pandas DataFrame

    params:
        track_layer: napari.layers.Tracks

    returns:
        df: pd.DataFrame

    also see:
        pd_to_napari_tracks
    """
    df = pd.DataFrame(track_layer.data, columns=Labels.track_header)
    if not hasattr(track_layer, 'properties'):
        warnings.warn(
            "Track layer does not have properties produsing tracking without properties")
        return df

    properties = track_layer.properties
    for property, values in properties.items():
        if property == Labels.track_id:
            continue
        df[property] = values
    return df


def pd_to_napari_tracks(df: pd.DataFrame):
    """
    This function converts pandas DataFrame to napari Tracks layer paramters
    params:
        df: pandas.DataFrame

    return:
        tracks: np.Array 2D [
            [track_id, time, (c), (z), y, x]
        ]
        properties: dict
        track_meta: pd.DataFrame
    also see:
        napari_track_to_pd
    """
    # assuming df is the dataframe with 'particle' as track_id
    tracks = []
    properties = {}

    columns = list(df.columns)

    for th in Labels.track_header:
        columns.remove(th)

    tg = df.groupby('track_id', as_index=False,
                    group_keys=True, dropna=True)
    track_meta = pd.concat([tg['frame'].count(),
                            tg['intensity_mean'].max()['intensity_mean'],
                            tg['intensity_mean'].mean()['intensity_mean'],
                            tg['intensity_mean'].min()['intensity_mean']], axis=1)
    track_meta.columns = Labels.track_meta_header

    properties = df[columns].to_dict()
    properties = dict(
        map(lambda kv: (kv[0], np.array(list(kv[1].values()))), properties.items()))

    tracks = df[Labels.track_header].to_numpy()

    return tracks, properties, track_meta


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
