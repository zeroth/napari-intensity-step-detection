from napari_intensity_step_detection.base.widget import NLayerWidget
from qtpy.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGridLayout, QScrollArea, QTabWidget
import napari
from napari.utils import notifications
import warnings
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.base.plots import Histogram, BaseMPLWidget, colors
from typing import Optional, Any, List
import numpy as np


def normalizeData(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def get_alfa_color(alfa):
    yellow = [255, 255, 0, 128]
    cyan = [0, 183, 235, 128]
    magenta = [255, 0, 255, 128]

    if alfa < 0.4:
        return normalizeData(np.array(yellow))
    elif 0.4 <= alfa <= 1.2:
        return normalizeData(np.array(cyan))
    else:
        return normalizeData(np.array(magenta))


def get_alfa_label(alfa):
    if alfa < 0.4:
        return 'alfa < 0.4'
    elif 0.4 <= alfa <= 1.2:
        return '0.4 < alfa < 1.2'
    else:
        return 'alfa > 1.2'


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


class MsdPlot(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self. data = None
        self.title = ""
        # self._setup_callbacks()
        self.add_single_axes()

    def setData(self, data, title):
        self.data = data
        self.title = title

    def draw(self) -> None:
        self.clear()
        """
        series = {
                'track_id': name,
                'msd': {'type': 'scatter', 'y': y, 'x': x},
                'msf_fit': {'type': 'line', 'y': _y, 'x': x}
                'alfa': alfa
            }
        """
        if isinstance(self.data, dict):
            self.axes.plot(self.data['x'], self.data['y'], color='b')

        else:
            for track in self.data:
                self.axes.scatter(track['msd']['x'], track['msd']['y'], color=colors[3])
                self.axes.plot(track['msf_fit']['x'], track['msf_fit']['y'],
                               color=get_alfa_color(track['alfa']))

        # self.axes.legend(loc='upper right')
        self.axes.set_title(label=self.title)

        # needed
        self.canvas.draw()


class TrackAnalysisResult(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(QGridLayout())

        self.layout().addWidget(self.scrollArea)
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
                    hist.setMinimumWidth(400)
                    hist.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(hist, row, col)
                elif value['type'] == 'msd_fit_plot':
                    msd_alfa = MsdAlfaPlot()
                    msd_alfa.setData(value['data'], title=f"{key}")
                    msd_alfa.draw()
                    msd_alfa.setMinimumWidth(400)
                    msd_alfa.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(msd_alfa, row, col)
                elif value['type'] == 'msd':
                    msd_plot = MsdPlot()
                    msd_plot.setData(value['data'], title=f"{key}")
                    msd_plot.draw()
                    msd_plot.setMinimumWidth(400)
                    msd_plot.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(msd_plot, row, col)
                elif value['type'] == 'alfa_hist':
                    hist = MsdPlot()
                    hist.setData(value['data'], title=f"{key}")
                    hist.draw()
                    hist.setMinimumWidth(400)
                    hist.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(hist, row, col)
        self.scrollArea.setWidget(self.centralWidget)


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
        self.result_tabs = QTabWidget()
        self.layout().addWidget(self.result_tabs)

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
            'length': {
                'type': 'histogram',
                'data': track_meta['length'].to_numpy()
            },
            'mean_intensity': {
                'type': 'histogram',
                'data': track_meta['intensity_mean'].to_numpy()
            }
        }

        tg = all_tracks.groupby('track_id', as_index=False, group_keys=True, dropna=True)
        msd = {'type': 'msd', 'data': []}
        msd_alfa = {
            'type': 'msd_fit_plot',
            'data': {
                "lt_0_4": [],
                "bt_0_4_1_2": [],
                "gt_1_2": []}
        }
        all_alfa = []

        for name, group in tg:
            track = group[['x', 'y']].to_numpy()
            y = utils.msd(track)
            x = np.array(list(range(1, len(y) + 1)))  # * 3.8

            alfa, _y = utils.basic_fit(y)
            all_alfa.append(alfa)

            series = {
                'track_id': name,
                'msd': {'type': 'scatter', 'y': y, 'x': x},
                'msf_fit': {'type': 'line', 'y': _y, 'x': x},
                'alfa': alfa
            }
            msd['data'].append(series)

            if alfa < 0.4:
                msd_alfa['data']['lt_0_4'].append(alfa)
            elif 0.4 < alfa < 1.2:
                msd_alfa['data']['bt_0_4_1_2'].append(alfa)
            elif alfa > 1.2:
                msd_alfa['data']['gt_1_2'].append(alfa)

        all_alfa_hist, _, _ = utils.histogram(all_alfa, 1)
        result_dict[track_layer.name]["msd"] = msd
        result_dict[track_layer.name]["msd_alfa"] = msd_alfa
        result_dict[track_layer.name]["all_alfa"] = {
            'type': 'alfa_hist',
            'data': {
                'y': all_alfa_hist, 'x': np.linspace(0, 2, len(all_alfa_hist))
            }
        }

        result_widget = TrackAnalysisResult()
        result_widget.set_result_dict(result_dict)
        result_widget.draw()
        self.result_tabs.addTab(result_widget, f"Results {track_layer.name}")
