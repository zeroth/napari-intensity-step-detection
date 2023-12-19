from pathlib import Path
from napari.utils import progress
from qtpy.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from qtpy.QtCore import QItemSelectionModel
from napari_intensity_step_detection.base import NLayerWidget, AppState
from napari_intensity_step_detection.tracking_widget.track_models import TrackMetaModel, TrackMetaModelProxy
from napari_intensity_step_detection.filter_widget.property_filter_widget import FilterWidget
from qtpy import uic
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import TrackLabels as Labels
import napari
import numpy as np
import pandas as pd


class ResultWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'step_analysis_result_widget.ui')
        self.load_ui(UI_FILE)
        self.btnExport.setIcon(utils.get_icon('file-export'))
        self.data = data
        self.setup_ui()

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setup_ui(self):
        step_meta: pd.DataFrame = self.data['steps_meta_df']
        step_info: pd.DataFrame = self.data['steps_df']
        data_dict = {}
        data_dict['step_count'] = step_meta['step_count'].to_numpy()
        data_dict['negetive_vs_positive'] = np.hstack([step_meta['negetive_steps'].to_numpy(),
                                                       step_meta['positive_steps'].to_numpy()])
        data_dict['single_step_height'] = np.abs(
            (step_meta[step_meta['step_count'] == 1]['step_height']).to_numpy())
        data_dict['max_intensity'] = step_meta['max_intensity'].to_numpy()
        data_dict['step_height'] = np.abs((self.data['steps_df']['step_height']).to_numpy())
        data_dict['track_length'] = step_meta['length'].to_numpy()

        # step length
        max_step_count = np.max(data_dict['step_count'])

        # for i in range(1, max_step_count+1):
        #     track_ids = (step_meta[step_meta['step_count'] == i]['track_id']).to_list()
        #     tracks_group = step_info[step_info['track_id'].isin(track_ids)].groupby('track_id')
        #     for j in range(0, i):
        #         jth = tracks_group['dwell_before'].nth(j).to_numpy(dtype=np.float64)
        #         data_dict[f'step_count_{i}_step_{j+1}_dwell_before'] = jth
        graph_dict = {}
        for i in range(1, max_step_count+1):
            track_ids = (step_meta[step_meta['step_count'] == i]['track_id']).to_list()
            tracks_group = step_info[step_info['track_id'].isin(track_ids)].groupby('track_id')
            graph_dict[f'step_count_{i}'] = {}
            for j in range(0, i):
                jth = tracks_group['dwell_before'].nth(j).to_numpy(dtype=np.float64)
                graph_dict[f'step_count_{i}'][f'step_{j+1}_length'] = jth

        data_dict['tile_histogram'] = graph_dict

        self.histogram.setData(data=data_dict)
        self.btnExport.clicked.connect(self.export)


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

    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer=napari_viewer, parent=parent)
        self.name = "tracking"
        # tracking controls
        self.filter_propery = 'length'
        self.tabWidget = QTabWidget(self)
        self.ui = _tracking_ui(self)
        self.tabWidget.addTab(self.ui, "Tracking")
        self.layout().addWidget(self.tabWidget)

        self.layer_filter["Tracks"] = napari.layers.Tracks

        self.ui.filterView.setLayout(QVBoxLayout())
        self.ui.btnTrack.clicked.connect(self.track)

    def setup_tracking_state(self, tracked_df, track_meta):
        print("setup_tracking_state")
        # self.state.setData(f"{self.name}", {"tracks_df": tracked_df, "meta_df": track_meta})
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
        # self.setup_tracking_state(tracked_df=tracked_df, track_meta=track_meta)
        # self.state.setData(f"{self.name}", {"tracks_df": tracked_df, "meta_df": track_meta})

        pbr.update(100)
        pbr.close()

        utils.add_track_to_viewer(self.state.viewer, Labels.tracks_layer, tracks, properties=properties,
                                  metadata={'all_meta': track_meta,
                                            'all_tracks': tracked_df,
                                            Labels.tracking_params: {
                                                "search_range": search_range,
                                                "memory": memory
                                            }
                                            })

    def update(self, data: dict):
        pass

    def get_data(self) -> dict:
        pass


# Comman functions


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
