import numpy as np
from typing import Optional, Any, List
from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from qtpy.QtWidgets import QVBoxLayout, QWidget, QAbstractItemView, QGridLayout
from qtpy.QtCore import QModelIndex, Qt, QRect, QPoint, Signal
from qtpy.QtGui import QRegion
from qtpy import uic
from pathlib import Path
from napari_intensity_step_detection import utils

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


class BaseMPLWidget(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        self.canvas = FigureCanvas()
        self.toolbar = NavigationToolbar2QT(
            self.canvas, parent=self
        )

        self.canvas.figure.set_layout_engine("constrained")

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
        self.count = count
        self.col = 2
        self.row = int(np.ceil(self.count/self.col))
        # print("add_multiple_axes", self.row, self.col)
        self.grid_space = self.figure.add_gridspec(ncols=self.col, nrows=self.row)
        # print("add_multiple_axes", self.grid_space)


class IntensityStepPlotsWidget(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """
        self.axes.clear()

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


class BinControlWidget(QWidget):
    editingFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'histogram_bin_control_widget.ui')
        self.load_ui(UI_FILE)
        self.sbControl.editingFinished.connect(self.editingFinished)

    def setTitle(self, text):
        self.lbTitle.setText(text)

    def title(self):
        return self.lbTitle.text()

    def setRange(self, vrange=(0, 1000)):
        vmin, vmax = vrange
        self.sbControl.setRange(vmin, vmax)

    def range(self):
        return (self.sbControl.minimum(), self.sbControl.maximum())

    def setValue(self, val):
        self.sbControl.setValue(val)

    def value(self):
        return self.sbControl.value()

    def load_ui(self, path):
        uic.loadUi(path, self)


class MultiHistogramWidgets(BaseMPLWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

    def clear(self) -> None:
        self.figure.clear()

    def draw(self) -> None:
        self.clear()
        if not hasattr(self, 'grid_space'):
            return
        n_colors = len(colors)
        # print(len(self.axes))
        for i, (key, val) in enumerate(self.data.items()):
            row = int(i / self.col)
            col = int(i % self.col)
            # print("MultiHistogramWidgets draw", row, col)
            y = np.array(val)
            hist, bins = utils.histogram(y, self.controls[key].value())
            ax = self.figure.add_subplot(self.grid_space[row, col])
            ax.hist(y.ravel(), bins=bins, edgecolor='black', color=colors[int(i % n_colors)])
            ax.set_title(label=key)
        # needed
        self.canvas.draw()

    def setData(self, data):
        self.data = data
        self.add_bin_controls()
        self.draw()

    def add_bin_controls(self):
        if hasattr(self, 'controls'):
            for k, v in self.controls.items():
                del v
            self.controls.clear()
            del self.controls
        if hasattr(self, 'control_toobar'):
            del self.control_toobar
        self.controls = {}
        self.control_toobar = QWidget(self)
        self.control_toobar.setMaximumHeight(105)
        self.control_toobar.setLayout(QGridLayout())
        self.layout().addWidget(self.control_toobar)
        col = 3
        for i, (key, val) in enumerate(self.data.items()):
            y = np.array(val)
            _control = BinControlWidget()
            _control.setTitle(key)
            _control.setRange((0, len(y)+1))
            _control.setValue(len(y)*0.01)
            self.controls[key] = _control
            _control.editingFinished.connect(self.draw)
            self.control_toobar.layout().addWidget(_control, int(i/col), int(i % col))


class HistogramWidget(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()
        self.data = []
        self.label = None
        self.color = None

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """
        self.axes.clear()

    def draw(self, data, label, bins=256, color=colors[1]) -> None:
        self.clear()
        if len(data):
            self.data = data
            self.label = label
            self.color = color
            y = np.array(self.data)
            self.axes.hist(y.ravel(), bins=bins, label=label)
            self.axes.legend(loc='upper right')

        # needed
        self.canvas.draw()


class HistogramPlotsWidget(BaseMPLWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """
        self.axes.clear()

    def draw(self, data) -> None:
        self.clear()
        print("HistogramPlotsWidget draw")
        n_colors = len(colors)
        for i, (p, v) in enumerate(data.items()):
            color = colors[int(i % n_colors)]
            value = np.array(v).ravel()
            # hist, _bin_e = np.histogram(value, bins=int(len(value)*0.1))
            # self.axes.plot(hist, color=color, label=p, alpha=0.5)
            self.axes.hist(value, color=color, label=p, alpha=0.5)
            self.axes.legend(loc='upper right')

        # needed
        self.canvas.draw()


class HistogramPlotsView(QAbstractItemView):
    def __init__(self, parent: Any = None):
        super().__init__(parent=parent)
        self.is_dirty = True
        self.row_count = 0
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.plot = HistogramPlotsWidget(self.viewport())
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)
        self.include_properties = []
        if (not self.plot.testAttribute(Qt.WidgetAttribute.WA_Resized)):
            self.plot.resize(self.plot.sizeHint())

        # self.plot.setAutoFillBackground(True)
        # self.plot.installEventFilter(self)
        self.plot.move(0, 0)
        self.plot.resize(self.viewport().rect().width(), self.viewport().rect().height())
        self.plot.show()

    def draw(self):
        self.plot.clear()

        data = {}
        for row in range(self.model().rowCount(self.rootIndex())):
            for col in range(1, self.model().columnCount(self.rootIndex())):
                index = self.model().index(row, col, self.rootIndex())
                val = float(self.model().data(index, Qt.ItemDataRole.DisplayRole))
                _property = self.model().headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
                if (len(self.include_properties)) and (_property not in self.include_properties):
                    continue
                if _property not in data:
                    data[_property] = [val]
                else:
                    data[_property].append(val)

        self.plot.draw(data=data)
        self.is_dirty = False

    def dataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: List[Any]):
        print("dataChanged")
        if Qt.ItemDataRole.DisplayRole not in roles:
            return
        # self.draw()
        self.is_dirty = True
        self.viewport().update()
        # super().dataChanged(self, topLeft, bottomRight, roles)

    def updateGeometries(self):
        # print("updateGeometries")
        # self.horizontalScrollBar().setPageStep(self.viewport().width())
        # self.horizontalScrollBar().setRange(0, self.viewport().width())
        # self.verticalScrollBar().setPageStep(self.viewport().height())
        # self.verticalScrollBar().setRange(0, self.viewport().height())
        self.plot.resize(self.viewport().rect().width(), self.viewport().rect().height())

    def verticalOffset(self):
        # print("verticalOffset")
        return self.verticalScrollBar().value()

    def horizontalOffset(self):
        # print("horizontalOffset")
        return self.horizontalScrollBar().value()

    # # Returns the position of the item in viewport coordinates.

    def visualRect(self, index: QModelIndex):
        # print("visualRect")
        if (not index.isValid()):
            return QRect()

        return self.viewport().rect()

    def indexAt(self, point: QPoint):
        # print("indexAt")
        return QModelIndex()

    def visualRegionForSelection(self, selection):
        return QRegion()

    def rowsInserted(self, parent, start, end):
        print("rowsInserted")
        self.is_dirty = True
        self.viewport().update()
        # super(HistogramPlotsView, self).rowsInserted(parent, start, end)

    def rowsAboutToBeRemoved(self, parent: QModelIndex, start: int, end: int):
        print("rowsAboutToBeRemoved")
        self.is_dirty = True
        self.viewport().update()
        # super(HistogramPlotsView, self).rowsAboutToBeRemoved(parent, start, end)

    def paintEvent(self, event):
        # print("paintEvent")
        # super().paintEvent(self, event)
        # TODO: check dirty
        if self.row_count == self.model().rowCount(self.rootIndex()):
            return
        self.row_count = self.model().rowCount(self.rootIndex())
        self.draw()

    def moveCursor(self, cursorAction, modifiers):
        return self.rootIndex()
