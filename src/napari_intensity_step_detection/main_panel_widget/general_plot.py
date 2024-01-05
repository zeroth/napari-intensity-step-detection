from napari_intensity_step_detection.base.plots import Histogram, BaseMPLWidget, colors
from typing import Optional
from qtpy.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QScrollArea, QLabel
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QDoubleValidator
from pathlib import Path
import numpy as np
from qtpy import uic
from napari_intensity_step_detection import utils


class DoubleBinSize(QWidget):
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


class GeneralPlot(BaseMPLWidget):
    def __init__(
        self,
        title,
        data,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self. data = data
        self.title = title

        self.add_single_axes()
        self.label = None
        self.color = colors[0]

    def add_bin_size_control(self):
        if hasattr(self, "control"):
            return
        self.control = DoubleBinSize()
        self.toolbar.addSeparator()
        self.control.setTitle("Bin Size")
        self.control.setValue(0.5)
        self.toolbar.addWidget(self.control)
        self.control.editingFinished.connect(self.draw)

        # if hasattr(self.toolbar, "coordinates"):
        #     self.toolbar.coordinates = False

    def setData(self, data):
        self.data = data
        # self.draw()

    def plot_line(self, data, _color=None):
        x = data.get('x', None)
        if x is None:
            self.axes.plot(
                data['y'], color=_color if _color else colors[0])
        else:
            self.axes.plot(data['x'], data['y'],
                           color=_color if _color else colors[0])

    def plot_scatter(self, data, _color=None):
        x = data.get('x', None)
        if x is None:
            self.axes.scatter(data['y'], marker='.', alpha=0.3, linewidths=0.5,
                              edgecolors='black', color=_color if _color else colors[0])
        else:
            self.axes.scatter(data['x'], data['y'], marker='.', alpha=0.3, linewidths=0.5,
                              edgecolors='black', color=_color if _color else colors[0])

    def plot_histline(self, data, _color=None):
        self.add_bin_size_control()
        hist, bins, binsize = utils.histogram(
            data['y'], self.control.value())
        self.axes.plot(bins[:-1], hist, color=colors[0])

    def plot_hist(self, data, _color=None):
        self.add_bin_size_control()
        hist, bins, binsize = utils.histogram(
            data['y'], self.control.value())
        self.axes.hist(data['y'], bins=bins, edgecolor='black',
                       linewidth=0.5, color=self.color, label=self.label)

    def draw_values(self, data):
        print(data.keys())
        if data['type'] == 'scatter':
            self.plot_scatter(data)
        elif data['type'] == 'line':
            self.plot_line(data)
        elif data['type'] == 'histline':
            self.plot_histline(data)
        elif data['type'] == 'histogram':
            self.plot_hist(data)
        else:
            raise Exception(f"Unknown plot type: {data['type']}")

    def draw(self) -> None:
        self.clear()

        x_label = self.data.get('x_label', None)
        y_label = self.data.get('y_label', None)
        if x_label is not None:
            self.axes.set_xlabel(x_label)
        if y_label is not None:
            self.axes.set_ylabel(y_label)

        if isinstance(self.data['data'], list):
            for data in self.data['data']:
                self.draw_values(data)
        else:
            self.draw_values(self.data['data'])

        # needed
        self.canvas.draw()
