import numpy as np
from typing import Optional, Any, List
from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine
from qtpy.QtWidgets import QVBoxLayout, QWidget, QAbstractItemView
from qtpy.QtCore import QModelIndex, Qt, QRect, QPoint, Signal
from qtpy.QtGui import QRegion, QIntValidator
from qtpy import uic
from pathlib import Path
from napari_intensity_step_detection import utils

import warnings
# from warnings import RuntimeWarning
warnings.filterwarnings('ignore', category=RuntimeWarning)

# colors = dict(
#     COLOR_1="#DC267F",
#     COLOR_2="#648FFF",
#     COLOR_3="#785EF0",
#     COLOR_4="#FE6100",
#     COLOR_5="#FFB000")

colors = list([
    "#DC267F",
    "#648FFF",
    "#785EF0",
    "#FE6100",
    "#FFB000"])


class HistogramBinSize(QWidget):
    editingFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'histogram_bin_control_widget.ui')
        self.load_ui(UI_FILE)
        self.leControl.editingFinished.connect(self.editingFinished)
        self.leControl.setValidator(QIntValidator())

    def setTitle(self, text):
        self.lbTitle.setText(text)

    def title(self):
        return self.lbTitle.text()

    def setValue(self, val):
        self.leControl.setText(str(val))

    def value(self):
        return int(self.leControl.text()) if self.leControl.text() else 0

    def load_ui(self, path):
        uic.loadUi(path, self)


class BaseMPLWidget(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        self.canvas = FigureCanvas(Figure(figsize=(40, 40)))
        self.toolbar = NavigationToolbar2QT(
            self.canvas, parent=self, coordinates=False
        )

        self.canvas.figure.set_layout_engine("constrained")
        # self.canvas.figure.set_layout_engine("compressed")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

    @property
    def figure(self) -> Figure:
        """Matplotlib figure."""
        return self.canvas.figure

    def add_single_axes(self) -> None:
        """
        Add a single Axes to the figure.

        The Axes is saved on the ``.axes`` attribute for later access.
        """
        self.axes = self.figure.subplots()

    def add_multiple_axes(self, count) -> None:
        """
        Add multiple Axes to the figure using count.
        The Axes is saved on the ``.axes`` attribute for later access.
        """
        self.figure.clear()
        self.count = count
        # self.col = count
        # self.row = count
        # # print("add_multiple_axes", self.row, self.col)
        self.grid_space = self.figure.add_gridspec(ncols=self.count, nrows=self.count, hspace=0, wspace=0)
        # params = self.grid_space.get_subplot_params()
        self.axes = self.grid_space.subplots(sharex='col', sharey='row')
        # self.axes = self.figure.subplots(count, count, sharex=True, sharey=True,
        #                                  gridspec_kw={'hspace': 0, 'wspace': 0})
        # print("add_multiple_axes", self.grid_space)
        # print("params : ", params.left, params.right, params.top, params.bottom, params.wspace, params.hspace)

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """
        # print("clear", type(self.axes))
        if isinstance(self.axes, np.ndarray):
            for ax in self.axes.ravel():
                ax.clear()
        else:
            self.axes.clear()


class IntensityStepPlots(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()

    def draw(self, intensity, fitx, title) -> None:
        self.clear()

        if len(intensity):
            _intensity = np.array(intensity)
            self.axes.plot(_intensity.ravel(), label="Intensity", color=colors[0])

        if len(fitx):
            _fitx = np.array(fitx)
            self.axes.plot(_fitx.ravel(), label="Steps", color=colors[1])

        self.axes.legend(loc='upper right')
        self.axes.set_title(label=title)

        # needed
        self.canvas.draw()


class Histogram(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()
        self.data = []
        self.label = None
        self.color = colors[0]
        self.control = HistogramBinSize()
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.control)
        self.control.setTitle("Bin Size")
        self.control.setValue(5)
        if hasattr(self.toolbar, "coordinates"):
            self.toolbar.coordinates = False

    def _get_dict_length(self, data):
        _size = []
        if isinstance(data, dict):
            for k, v in data.items():
                _size.append(len(v))
            return np.max(_size)

    def setData(self, data, title):
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = np.array(data).ravel()
            self.control.setValue(5 if len(data) > 5 else 2)

        self.label = title
        self.control.editingFinished.connect(self.draw)

    def setColor(self, color):
        self.color = color

    def draw(self) -> None:
        self.clear()

        if isinstance(self.data, dict):
            n_colors = len(colors)
            for i, (p, v) in enumerate(self.data.items()):
                color = colors[int(i % n_colors)]
                value = np.array(v).ravel()
                # hist, _bin_e = np.histogram(value, bins=int(len(value)*0.1))
                # self.axes.plot(hist, color=color, label=p, alpha=0.5)
                hist, bins, binsize = utils.histogram(value, self.control.value())
                # self.control.setValue(binsize)
                self.axes.hist(value, bins=bins, edgecolor='black', linewidth=0.5, color=color, label=p, alpha=0.5)
                self.axes.legend(loc='upper right')
        else:
            if len(self.data):
                hist, bins, binsize = utils.histogram(self.data, self.control.value())
                # self.control.setValue(binsize)
                self.axes.hist(self.data, bins=bins, edgecolor='black',
                               linewidth=0.5, color=self.color, label=self.label)
                self.axes.set_title(label=self.label)
                self.axes.legend(loc='upper right')

        # needed
        self.canvas.draw()


class HistogramMultiAxes(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        count: int = 1
    ):
        super().__init__(parent=parent)
        self.canvas.figure.set_layout_engine("constrained")
        bb = self.figure.get_tightbbox()
        print("canvas.get_width_height()", self.canvas.get_width_height())

        print("bounds ", bb.bounds)
        print("extents ", bb.extents)

        # self._setup_callbacks()
        self.add_multiple_axes(count=count)
        self.data = []
        self.label = None
        self.color = colors[0]
        self.control = HistogramBinSize()
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.control)
        self.control.setTitle("Bin Size")
        self.control.setValue(5)
        if hasattr(self.toolbar, "coordinates"):
            self.toolbar.coordinates = False

    def _get_dict_length(self, data):
        _size = []
        if isinstance(data, dict):
            for k, v in data.items():
                _size.append(len(v))
            return np.max(_size)

    def setData(self, data, title):
        self.data = data
        self.label = title
        self.control.editingFinished.connect(self.draw)

    def setColor(self, color):
        self.color = color

    def draw(self) -> None:
        self.clear()
        n_colors = len(colors)
        i_max = len(self.data) - 1

        first_axes = self.axes[0, 0]
        last_axes = self.axes[i_max, 0]

        self.figure.suptitle(self.label)
        #  , ha='center', va='bottom', y=first_axes._position.y1 + (first_axes._position.y1 * 0.03))
        self.figure.supylabel("Step Count")
        #   , va='center', ha='center', x=first_axes._position.x0 - (first_axes._position.x0*0.4))
        self.figure.supxlabel("Frequency")
        #  , ha='center', y=last_axes._position.x0 - (last_axes._position.x0*0.4))

        for i, (key, val) in enumerate(self.data.items()):
            for j, (k, v) in enumerate(val.items()):
                # print(f"HistogramMultiAxes : drawing {i}, {j}, {k}")
                color = colors[int(j % n_colors)]
                hist, bins, binsize = utils.histogram(v, self.control.value())
                self.axes[i, j].hist(v, bins=bins, edgecolor='black', linewidth=0.5,
                                     color=color, label=k, alpha=0.5, orientation='horizontal')

                # space_axes[i, j].invert_yaxis()
                if j == 0:
                    self.axes[i, j].set_ylabel(f"Total steps {i+1}")
                if i == i_max:
                    self.axes[i, j].set_xlabel(f"step {j+1}")
        # needed
        self.canvas.draw()
