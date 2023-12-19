from napari_intensity_step_detection.base.widget import NLayerWidget
from qtpy.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGridLayout
import napari
from napari.utils import notifications
import warnings
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.base.plots import Histogram, BaseMPLWidget, colors
from typing import Optional, Any, List


class MsdAlfaPlot(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self. msf_alfa = {}
        self.title = ""
        # self._setup_callbacks()
        self.add_single_axes()

    def setData(self, data, title):
        self.msf_alfa = data
        self.title = title

    def draw(self) -> None:
        self.clear()

        for i, (name, data) in enumerate(self.msf_alfa.items()):
            self.axes.plot(data, label=name, color=colors[i])

        self.axes.legend(loc='upper right')
        self.axes.set_title(label=self.title)

        # needed
        self.canvas.draw()


class TrackAnalysisResult(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QGridLayout())
        self.col = 2

    def set_result_dict(self, result):
        self.result_dict = result
        self.draw()

    def draw(self):
        for name, data in self.result_dict.items():
            for i, (key, value) in enumerate(data.items()):
                row = int(i / self.col)
                col = int(i % self.col)
                if value['type'] == 'histogram':
                    hist = Histogram()
                    hist.setData(value['data'], title=f"{name}", label=f"{key}")
                    hist.draw()
                    self.layout().addWidget(hist, row, col)
                elif value['type'] == 'msd_fit_plot':
                    msd_alfa = MsdAlfaPlot()
                    msd_alfa.setData(value['data'], title=f"{name} {key}")
                    msd_alfa.draw()
                    self.layout().addWidget(msd_alfa, row, col)


class TrackAnalysis(NLayerWidget):
    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer, parent)

        # set layer filter
        self.layer_filter = {"Track": napari.layers.Tracks}
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze)

        def viewer_layer_updated(event):
            for name, dtype in self.layer_filter.items():
                if isinstance(event.value, dtype):
                    self.nLayersLayout.addRow("...", self.analyze_button)
        self.nLayerInserted.connect(viewer_layer_updated)

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
        result_dict[track_layer.name] = {
            'length': {'type': 'histogram', 'data': track_meta['length'].to_numpy()},
            'mean_intensity': {'type': 'histogram', 'data': track_meta['intensity_mean'].to_numpy()}
        }

        tg = all_tracks.groupby('track_id', as_index=False, group_keys=True, dropna=True)
        msd = {}
        msd_alfa = {
            'type': 'msd_fit_plot',
            'data': {
                "lt_0_4": [],
                "bt_0_4_1_2": [],
                "gt_1_2": []}
        }

        for name, group in tg:
            track = group[['x', 'y']].to_numpy()

            msd[name] = utils.msd(track)

            alfa, _y = utils.basic_fit(msd[name])
            if alfa < 0.4:
                msd_alfa['data']['lt_0_4'].append(alfa)
            elif 0.4 < alfa < 1.2:
                msd_alfa['data']['bt_0_4_1_2'].append(alfa)
            elif alfa > 1.2:
                msd_alfa['data']['gt_1_2'].append(alfa)

        result_dict[track_layer.name]["msd"] = {'type': 'plot', 'data': []}
        result_dict[track_layer.name]["msd"]['data'] = msd
        result_dict[track_layer.name]["msd_alfa"] = msd_alfa

        result_widget = TrackAnalysisResult()
        result_widget.set_result_dict(result_dict)
        result_widget.draw()
        self.layout().addWidget(result_widget)
