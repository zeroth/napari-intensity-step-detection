from napari_intensity_step_detection.base.plots import Histogram, BaseMPLWidget, colors
from typing import Optional
from qtpy.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QVBoxLayout, QGridLayout, QScrollArea, QLabel, QDoubleSpinBox, QPushButton, QFrame
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QDoubleValidator, QIntValidator
from pathlib import Path
import numpy as np
from qtpy import uic
from napari_intensity_step_detection import utils
from matplotlib.lines import Line2D


class BinSizeControl(QWidget):
    editingFinished = Signal()

    def __init__(self, precision='double', parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.lbTitle = QLabel()
        self.layout().addWidget(self.lbTitle)
        self.leControl = QLineEdit()
        self.layout().addWidget(self.leControl)
        self.leControl.editingFinished.connect(self.editingFinished)
        if precision == 'double':
            self.leControl.setValidator(QDoubleValidator())
        else:
            self.leControl.setValidator(QIntValidator())

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
        data=None,
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
        self.control = BinSizeControl(precision='double')
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

    def plot_line(self, data, color=None):
        x = data.get('x', None)
        if x is None:
            self.axes.plot(
                data['y'], color=color if color else colors[0])
        else:
            self.axes.plot(data['x'], data['y'],
                           color=color if color else colors[0])

    def plot_scatter(self, data, color=None):
        x = data.get('x', None)
        if x is None:
            self.axes.scatter(data['y'], marker='.', alpha=0.3, linewidths=0.5,
                              edgecolors='black', color=color if color else colors[1])
        else:
            self.axes.scatter(data['x'], data['y'], marker='.', alpha=0.3, linewidths=0.5,
                              edgecolors='black', color=color if color else colors[1])

    def plot_histline(self, data, color=None):
        self.add_bin_size_control()
        hist, bins, binsize = utils.histogram(
            data['y'], self.control.value())
        _range = data.get('range', None)
        legends = data.get('legends', None)
        if _range:
            _range.insert(0, bins[0])
            _range.append(bins[-1])

        self.axes.plot(bins[:-1], hist, color=color if color else colors[2])

        if _range:
            legends_labels = []
            for index in range(1, len(_range)):
                c = colors[int(index % len(colors))]
                self.axes.axvspan(_range[index-1], _range[index],
                                  alpha=0.3, color=c)
                legends_labels.append(
                    Line2D([0], [0], color=c, lw=4))
            # self.axes.get_legend().remove()
            self.axes.legend(
                legends_labels, legends, loc='upper right', framealpha=0.5, title_fontsize='x-small')
            # _range_str = [f"{_range[i]:.2f}" for i in range(len(_range))]
            # self.axes.set_xticks(_range, labels=_range_str, fontsize='x-small')

    def plot_hist(self, data, color=None):
        self.add_bin_size_control()
        label = data.get('label', None)
        hist, bins, binsize = utils.histogram(
            data['y'], self.control.value())
        self.axes.hist(data['y'], bins=bins, edgecolor='black',
                       linewidth=0.5, color=color if color else colors[3], label=label)
        self.axes.legend()

    def draw_values(self, data, color=None):
        if data['type'] == 'scatter':
            self.plot_scatter(data, color=color)
        elif data['type'] == 'line':
            self.plot_line(data, color=color)
        elif data['type'] == 'histline':
            self.plot_histline(data, color=color)
        elif data['type'] == 'histogram':
            self.plot_hist(data, color=color)
        else:
            raise Exception(f"Unknown plot type: {data['type']}")

    def draw(self) -> None:
        self.clear()

        x_label = self.data.get('x_label', None)
        y_label = self.data.get('y_label', None)
        title = self.data.get('title') if self.data.get(
            'title', None) is not None else self.title
        if title is not None:
            self.axes.set_title(title)
        if x_label is not None:
            self.axes.set_xlabel(x_label)
        if y_label is not None:
            self.axes.set_ylabel(y_label)

        if isinstance(self.data['data'], list):
            for i, data in enumerate(self.data['data']):
                self.draw_values(data, color=colors[i % len(colors)])
        else:
            self.draw_values(self.data['data'])

        # needed
        self.canvas.draw()

    def get_config(self):
        if hasattr(self, "control"):
            return {
                'data': self.data,
                'bin_size': self.control.value()
            }
        else:
            return None


class StepDetectionPlot(QWidget):
    createSteps = Signal(float, int)

    def __init__(self, title, parent=None):
        super().__init__(parent=parent)
        self.track = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.controlWidget = QWidget()
        self.controlWidget.setLayout(QHBoxLayout())
        self.controlWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.controlWidget.layout().addWidget(QLabel("Threshold"))
        self.sbThreshold = QDoubleSpinBox()
        self.sbThreshold.setRange(0, 1)
        self.sbThreshold.setSingleStep(0.01)
        self.sbThreshold.setValue(0.5)
        self.controlWidget.layout().addWidget(self.sbThreshold)

        self.controlWidget.layout().addWidget(QLabel("Window Size"))
        self.leWindowSize = QLineEdit()
        self.leWindowSize.setText(str(5))
        self.leWindowSize.setValidator(QIntValidator())
        self.controlWidget.layout().addWidget(self.leWindowSize)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.controlWidget.layout().addWidget(separator)

        self.applyButton = QPushButton("Apply All")
        self.controlWidget.layout().addWidget(self.applyButton)

        def apply_all():
            self.createSteps.emit(self.sbThreshold.value(),
                                  int(self.leWindowSize.text()))
        self.applyButton.clicked.connect(apply_all)

        self.plot = GeneralPlot(title=title, data=None)
        self.warning_label = QLabel("Track should me minimum 10 frames long")
        self.layout().addWidget(self.warning_label)
        self.layout().addWidget(self.plot)
        self.layout().addWidget(self.controlWidget)

        self.warning_label.setVisible(False)

        self.sbThreshold.valueChanged.connect(self.draw_track)
        self.leWindowSize.editingFinished.connect(self.draw_track)

    def set_track(self, track):
        self.track = track

    def draw_track(self):
        if self.track is None:
            return
        if self.track.length < 10:
            self.warning_label.setVisible(True)
            return
        else:
            self.warning_label.setVisible(False)

        steps, fitx, _ = self.track.step_detection(window=int(
            self.leWindowSize.text()), threshold=self.sbThreshold.value())

        mean_intensity = self.track.intensity()
        x = np.arange(0, len(mean_intensity)) * self.track.delta
        _track = {
            'x_label': 'Time (s)',
            'y_label': 'Intensity & Steps',
            'title': f'Track: {str(self.track.track_id)} - Step fitting',
            'data': [
                {
                    'x': x,
                    'y': mean_intensity,
                    'type': 'line',
                    'label': 'Intensity'
                },
                {
                    'x': x,
                    'y': fitx,
                    'type': 'line',
                    'label': 'Steps'
                }
            ]
        }
        self.plot.setData(_track)
        self.plot.draw()

    def get_config(self):
        return {
            'threshold': self.sbThreshold.value(),
            'window_size': int(self.leWindowSize.text())
        }
