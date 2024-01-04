from napari_intensity_step_detection.base.plots import Histogram, BaseMPLWidget, colors
from typing import Optional
from qtpy.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QDoubleValidator
from pathlib import Path
import numpy as np
from qtpy import uic
from napari_intensity_step_detection import utils


def get_alfa_color(alfa):
    yellow = "#ffff0008"  # [255, 255, 0, 128]
    cyan = "#00b7eb80"  # [0, 183, 235, 128]
    magenta = "#ff00ff80"  # [255, 0, 255, 128]

    if alfa < 0.4:
        return yellow
    elif 0.4 <= alfa <= 1.2:
        return cyan
    else:
        return magenta


def get_alfa_label(alfa):
    if alfa < 0.4:
        return 'alfa < 0.4'
    elif 0.4 <= alfa <= 1.2:
        return '0.4 < alfa < 1.2'
    else:
        return 'alfa > 1.2'


class MSDAlphaBinSize(QWidget):
    editingFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'histogram_bin_control_widget.ui')
        self.load_ui(UI_FILE)
        self.leControl.editingFinished.connect(self.editingFinished)
        self.leControl.setValidator(QDoubleValidator())

    def setTitle(self, text):
        self.lbTitle.setText(text)

    def title(self):
        return self.lbTitle.text()

    def setValue(self, val):
        self.leControl.setText(str(val))

    def value(self):
        return float(self.leControl.text()) if self.leControl.text() else 0

    def load_ui(self, path):
        uic.loadUi(path, self)


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

    def set_subtypes(self, subtypes):
        self.subtypes = subtypes

    def draw(self) -> None:
        self.clear()
        # if isinstance(self.data, dict):
        # print("MsdPlot ", self.data.keys())
        if self.data.get('series', None) is None:
            # self.axes.plot(self.data['x'], self.data['y'], color='b')
            self.plot_axis(self.data, _color=colors[3])

        else:
            for series in self.data['series']:
                for mode, data in series.items():
                    if mode == 'msd':
                        self.plot_axis(data, _color=colors[3])
                    elif mode == 'msf_fit':
                        self.plot_axis(data, _color=get_alfa_color(series['alfa']))
                    elif mode == 'inteinsity':
                        self.plot_axis(data, _color=colors[1])
            self.axes.set_xlabel(self.data['x_label'])
            self.axes.set_ylabel(self.data['y_label'])

        self.axes.set_title(label=self.title)

        # needed
        self.canvas.draw()

    def plot_axis(self, data, _color=None):
        # print("plot_axis ", data['type'], len(data['y']))
        if data['type'] == 'scatter':
            x = data.get('x', None)
            if x is None:
                self.axes.scatter(data['y'], marker='.', alpha=0.3, linewidths=0.5,
                                  edgecolors='black', color=_color if _color else colors[0])
            else:
                self.axes.scatter(data['x'], data['y'], marker='.', alpha=0.3, linewidths=0.5,
                                  edgecolors='black', color=_color if _color else colors[0])
        elif data['type'] == 'line':
            x = data.get('x', None)
            if x is None:
                self.axes.plot(data['y'], color=_color if _color else colors[0])
            else:
                self.axes.plot(data['x'], data['y'], color=_color if _color else colors[0])
        vspan_range = data.get('range', None)
        if vspan_range is not None:
            for index in range(1, len(vspan_range)):
                self.axes.axvspan(vspan_range[index-1], vspan_range[index],
                                  alpha=0.3, color=colors[int(index % len(colors))])

        x_label = data.get('x_label', None)
        if x_label is not None:
            self.axes.set_xlabel(x_label)
        y_label = data.get('y_label', None)
        if y_label is not None:
            self.axes.set_ylabel(y_label)


class MsdAlphaPlot(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self. data = None
        self.title = ""
        # self._setup_callbacks()
        self.add_single_axes()
        self.label = None
        self.color = colors[0]
        self.control = MSDAlphaBinSize()
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.control)
        self.control.setTitle("Bin Size")
        self.control.setValue(0.5)
        if hasattr(self.toolbar, "coordinates"):
            self.toolbar.coordinates = False

    def setData(self, data, title):
        self.data = data
        self.title = title
        self.control.editingFinished.connect(self.draw)

    def set_subtypes(self, subtypes):
        self.subtypes = subtypes

    def draw(self) -> None:
        self.clear()
        # self.axes.plot(self.data['x'], self.data['y'], color='b')
        # self.plot_axis(self.data, _color=colors[3])

        hist, bins, binsize = utils.histogram(self.data['y'], self.control.value())
        # self.control.setValue(binsize)
        # self.axes.hist(self.data, bins=bins, edgecolor='black',
        #                linewidth=0.5, color=self.color, label=self.label)
        self.axes.plot(bins[:-1], hist, color=colors[0])
        # self.axes.set_title(label=self.title)
        self.axes.legend(loc='upper right')

        self.axes.set_xlabel(self.data['x_label'])
        self.axes.set_ylabel(self.data['y_label'])

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

        self.title = 'Untitled'

    def set_title(self, title):
        self.title = title

    def set_result_dict(self, result):
        self.result_dict = result
        self.draw()

    def draw(self):
        title_labled = QLabel()
        title_labled.setTextFormat(1)
        title_labled.setText(f"<center><h2>{' '.join(self.title.split(' ')[:-1])}</h2></center>")
        title_labled.setAlignment(Qt.AlignCenter)
        title_labled.setStyleSheet("QLabel { background-color : white; color : black; }")
        self.centralWidget.layout().addWidget(title_labled, 0, 0, 1, -1)
        for name, data in self.result_dict.items():
            for i, (key, value) in enumerate(data.items()):
                row = int((i+2) / self.col)
                col = int((i+2) % self.col)

                if value['type'] == 'histogram':
                    hist = Histogram()
                    hist.setData(value['data']['y'], title=f"{key}", label=f"{key}")
                    hist.setXAxisLabel(value['data']['x_label'])
                    hist.setYAxisLabel(value['data']['y_label'])
                    hist.draw()
                    hist.setMinimumWidth(400)
                    hist.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(hist, row, col)
                elif value['type'] == 'msd_fit_alfa':
                    plot = MsdAlphaPlot()
                    plot.setData(value['data'], title=f"{key}")
                    plot.draw()
                    plot.setMinimumWidth(400)
                    plot.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(plot, row, col)
                else:
                    msd_plot = MsdPlot()
                    msd_plot.setData(value['data'], title=f"{key}")
                    msd_plot.draw()
                    msd_plot.setMinimumWidth(400)
                    msd_plot.setMinimumHeight(400)
                    self.centralWidget.layout().addWidget(msd_plot, row, col)
        self.scrollArea.setWidget(self.centralWidget)

# (value['type'] == 'msd') or (value['type'] == 'intensity_graph')\
#                         or (value['type'] == 'lifetime_vs_intensity') or (value['type'] == 'alfa_hist') or (value['type'] == 'msd_fit_alfa')
