from qtpy.QtWidgets import QVBoxLayout, QWidget, QTabWidget
from .segmentation_widget.segmentation_widget import SegmentationWidget
from .tracking_widget.tracking_widget import TrackingWidget
from .step_analysis_widget.stepanalysis_widget import StepAnalysisWidget
from .filter_widget.property_filter_widget import PropertyFilter


class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.segmentation_widget = SegmentationWidget(napari_viewer)
        self.tracking_widget = TrackingWidget(napari_viewer)
        self.property_filter_widget = PropertyFilter(napari_viewer)
        self.stepanalysis_widget = StepAnalysisWidget()
        self.setLayout(QVBoxLayout())
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)

        # segmentation_widget = QWidget()
        # segmentation_widget.setLayout(QVBoxLayout())
        # title = QLabel("<h2><u>Segmentation</u></h2>")
        # title.setTextFormat(Qt.TextFormat.RichText)
        # segmentation_widget.layout().addWidget(title)
        # segmentation_widget.layout().addWidget(self.segmentation_widget)

        # tracking_widget = QWidget()
        # tracking_widget.setLayout(QVBoxLayout())
        # title = QLabel("<h2><u>Tracking</u></h2>")
        # title.setTextFormat(Qt.TextFormat.RichText)
        # tracking_widget.layout().addWidget(title)
        # tracking_widget.layout().addWidget(self.tracking_widget)

        # stepanalysis_widget = QWidget()
        # stepanalysis_widget.setLayout(QVBoxLayout())
        # title = QLabel("<h2><u>Step Analysis</u></h2>")
        # title.setTextFormat(Qt.TextFormat.RichText)
        # stepanalysis_widget.layout().addWidget(title)
        # stepanalysis_widget.layout().addWidget(self.stepanalysis_widget)

        self.tabs.addTab(self.segmentation_widget, "Segmentation")
        self.tabs.addTab(self.tracking_widget, "Tracking")
        self.tabs.addTab(self.property_filter_widget, "Properties Filter")
        self.tabs.addTab(self.stepanalysis_widget, "Step Analysis")
