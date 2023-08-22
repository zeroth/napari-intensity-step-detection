import numpy as np
from typing import Optional, Any, List
from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from qtpy.QtWidgets import QVBoxLayout, QWidget, QAbstractItemView
from qtpy.QtCore import QModelIndex, Qt, QRect, QPoint


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
        self.is_dirty = False
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
        super(HistogramPlotsView, self).visualRegionForSelection(selection)

    def rowsInserted(self, parent, start, end):
        # print("rowsInserted")
        self.is_dirty = True
        super(HistogramPlotsView, self).rowsInserted(parent, start, end)
        self.viewport().update()

    def rowsAboutToBeRemoved(self, parent: QModelIndex, start: int, end: int):
        # print("rowsAboutToBeRemoved")
        self.is_dirty = True
        super(HistogramPlotsView, self).rowsAboutToBeRemoved(parent, start, end)
        self.viewport().update()

    def paintEvent(self, event):
        # print("paintEvent")
        # super().paintEvent(self, event)
        # TODO: check dirty
        if not self.is_dirty:
            return super(HistogramPlotsView, self).paintEvent(event)
        if not self.model():
            return super(HistogramPlotsView, self).paintEvent(event)
        self.draw()

    def moveCursor(self, cursorAction, modifiers):
        super(HistogramPlotsView, self).moveCursor(cursorAction, modifiers)
