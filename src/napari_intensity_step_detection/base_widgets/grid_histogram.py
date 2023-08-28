from napari_intensity_step_detection.base_widgets.plots import colors, HistogramWidget
from qtpy.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout, QSizePolicy
from typing import Optional


class GrigHistogramWidgets(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.setLayout(QVBoxLayout())

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(QGridLayout())
        # self.centralWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # self.layout().addWidget(self.centralWidget)
        self.layout().addWidget(self.scrollArea)
        self.col = 2

    def draw(self) -> None:
        n_colors = len(colors)
        # print(len(self.axes))
        for i, (key, val) in enumerate(self.data.items()):
            row = int(i / self.col)
            col = int(i % self.col)
            # print("MultiHistogramWidgets draw", row, col)
            _histogram = HistogramWidget()
            _histogram.setMinimumWidth(400)
            _histogram.setMinimumHeight(400)
            _histogram.setData(val, key)
            _histogram.setColor(colors[int(i % n_colors)])
            _histogram.draw()
            self.centralWidget.layout().addWidget(_histogram, row, col)
        self.scrollArea.setWidget(self.centralWidget)

    def setData(self, data):
        self.data = data
        self.draw()


def main():
    from qtpy.QtWidgets import QApplication
    import sys
    import numpy as np
    app = QApplication(sys.argv)
    d1 = np.linspace(10, 20, 100)
    d2 = np.linspace(100, 200, 50)
    d3 = np.linspace(1000, 2000, 500)
    data = {
        "d1": d1,
        "d2": d2,
        "d3": d3
    }
    gh = GrigHistogramWidgets()
    gh.setData(data=data)
    gh.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
