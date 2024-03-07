import napari
from qtpy.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from napari_intensity_step_detection.base.widget import NLayerWidget
import napari_intensity_step_detection.utils as utils
from pathlib import Path
from .quick_annotation_widget import QuickAnnotation
from .walking_average_widget import WalkingAverage
from .segmentation_widget import Segmentation
from .tracking_widget import Tracking


class _main_panel_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.joinpath('main_panel.ui')
        utils.load_ui(UI_FILE, self)


class MainPanel(NLayerWidget):
    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(napari_viewer, parent)
        self.ui = _main_panel_ui(self)
        self.layout().addWidget(self.ui)

        # set layer filter
        self.layer_filter = {"Image": napari.layers.Image,
                             "Label": napari.layers.Labels,
                             "Track": napari.layers.Tracks,
                             "Shape": napari.layers.Shapes}

        self.ui.panel_widget.setLayout(QVBoxLayout())
        self.ui.panel_widget.layout().setContentsMargins(0, 0, 0, 0)

        # create tool box
        self.tool_box = QTabWidget()
        self.tool_box.setTabPosition(QTabWidget.West)
        self.ui.panel_widget.layout().addWidget(self.tool_box)

        # create widgets
        self.walking_average = WalkingAverage(self)
        self.walking_average.layout().addStretch()
        self.tool_box.addTab(self.walking_average, "Walking Average")

        self.quick_annotation = QuickAnnotation(self)
        self.quick_annotation.layout().addStretch()
        self.tool_box.addTab(self.quick_annotation, "Quick Annotation")

        self.segmentation = Segmentation(self)
        self.segmentation.layout().addStretch()
        self.tool_box.addTab(self.segmentation, "Segmentation")

        self.tracking = Tracking(self)
        self.tool_box.addTab(self.tracking, "Tracking")

    def add_tab(self, widget, name):
        self.tool_box.addTab(widget, name)
