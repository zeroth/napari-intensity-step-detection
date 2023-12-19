from qtpy import uic
from pathlib import Path
from qtpy.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QGroupBox, QVBoxLayout, QSizePolicy
from qtpy.QtCore import Signal
from qtpy.QtGui import QIntValidator
from superqt import QRangeSlider
from qtpy.QtCore import Qt, QSize, QTimer


class _h_slider_ui(QWidget):
    valueChanged = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(parent.sizePolicy().hasHeightForWidth())
        parent.setSizePolicy(sizePolicy)

        # self.horizontalLayout_3 = QHBoxLayout()
        # self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        # self.horizontalLayout_3.setSpacing(2)
        # self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.setLayout(QVBoxLayout())
        self.group = QGroupBox()
        self.layout().addWidget(self.group)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(2)

        self.group_layout = QHBoxLayout()
        self.hSlider = QRangeSlider(Qt.Horizontal)
        self.leMin = QLineEdit()
        lmsizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lmsizePolicy.setHorizontalStretch(0)
        lmsizePolicy.setVerticalStretch(0)
        lmsizePolicy.setHeightForWidth(self.leMin.sizePolicy().hasHeightForWidth())
        self.leMin.setSizePolicy(lmsizePolicy)
        self.leMin.setMaximumSize(QSize(30, 16777215))
        self.leMin.setFocusPolicy(Qt.ClickFocus)
        self.leMin.setFrame(False)

        self.leMax = QLineEdit()
        lemsizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lemsizePolicy.setHorizontalStretch(0)
        lemsizePolicy.setVerticalStretch(0)
        lemsizePolicy.setHeightForWidth(self.leMax.sizePolicy().hasHeightForWidth())
        self.leMax.setSizePolicy(lemsizePolicy)
        self.leMax.setMaximumSize(QSize(30, 16777215))
        self.leMax.setFocusPolicy(Qt.ClickFocus)
        self.leMax.setFrame(False)

        self.group_layout.addWidget(self.leMin)
        self.group_layout.addWidget(self.hSlider)
        self.group_layout.addWidget(self.leMax)
        self.group.setLayout(self.group_layout)
        self.group_layout.setContentsMargins(0, 0, 0, 0)
        self.group_layout.setSpacing(2)

        self.leMin.setStyleSheet("background:transparent; border: 0;")
        self.leMax.setStyleSheet("background:transparent; border: 0;")

        self.leMin.setValidator(QIntValidator())
        self.leMax.setValidator(QIntValidator())
        self.hSlider.valueChanged.connect(self._update_labels)
        self.hSlider.valueChanged.connect(self.valueChanged)
        self.leMin.editingFinished.connect(self._update_min)
        self.leMax.editingFinished.connect(self._update_max)

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setRange(self, vrange):
        vmin, vmax = vrange
        if vmin == vmax:
            vmax = vmin+1
        self.leMin.setText(str(vmin))
        self.leMax.setText(str(vmax))
        self.hSlider.setRange(vmin, vmax)

    def range(self):
        return (self.hSlider.minimum(), self.hSlider.maximum())

    def setValue(self, vrange):
        if vrange[0] == vrange[1]:
            vrange = (vrange[0], vrange[0]+1)
        self.hSlider.setValue(vrange)

    def value(self):
        return self.hSlider.value()

    def _update_labels(self, vrange):
        vmin, vmax = vrange
        self.leMin.setText(str(vmin))
        self.leMax.setText(str(vmax))

    def _update_min(self):
        text = self.leMin.text()
        vmin, vmax = self.hSlider.value()
        rmin, _ = self.hSlider.minimum(), self.hSlider.maximum()
        val = int(text) if text else rmin
        self.setValue((val, vmax))

    def _update_max(self):
        text = self.leMax.text()
        vmin, vmax = self.hSlider.value()
        _, rmax = self.hSlider.minimum(), self.hSlider.maximum()
        val = int(text) if text else rmax
        self.setValue((vmin, val))

    def setTracking(self, state: bool):
        self.hSlider.setTracking(state)

    def tracking(self):
        return self.hSlider.tracking()


class HRangeSlider(QWidget):
    """
    Horizontal slider
    """
    valueChanged = Signal(tuple)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout()
        self.ui = _h_slider_ui(self)
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.setTracking(False)
        self.ui.valueChanged.connect(self.valueChanged)

    def setRange(self, vrange):
        self.ui.setRange(vrange)

    def setValue(self, vrange):
        self.ui.setValue(vrange)

    def value(self):
        return self.ui.value()

    def range(self):
        return self.ui.range()

    def setTracking(self, state: bool):
        self.ui.setTracking(state)

    def setTitle(self, title):
        self.ui.group.setTitle(f"{title}")


class HFilterSlider(HRangeSlider):
    valueChangedTitled = Signal(str, tuple)

    def __init__(self, title: str = 'untitled', parent: QWidget = None) -> None:
        super().__init__(parent)
        self.valueChanged.connect(self.valueUpdated)
        self.title = title
        self.setTitle(f"Filter: {title}")

    def valueUpdated(self, vrange):
        self.valueChangedTitled.emit(self.title, vrange)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = HRangeSlider()
    widget.setRange((0, 100))
    widget.setValue((0, 100))
    widget.show()
    sys.exit(app.exec())
