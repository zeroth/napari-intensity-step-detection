from qtpy.QtWidgets import QVBoxLayout, QWidget, QTabWidget
from .segmentation_widget import SegmentationWidget
from .tracking_widget import TrackingWidget
from .filter_widget import PropertyFilterWidget
from .base_widgets import AppState

from .step_analysis_widget.stepanalysis_widget import StepAnalysisWidget



class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.app_state = AppState(napari_viewer=napari_viewer)

        self.segmentation_widget = SegmentationWidget(app_state=self.app_state)
        self.tracking_widget = TrackingWidget(app_state=self.app_state)
        self.property_filter_widget = PropertyFilterWidget(app_state=self.app_state)
        # self.stepanalysis_widget = StepAnalysisWidget()
        self.setLayout(QVBoxLayout())
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)
        self.tabs.addTab(self.segmentation_widget, "Segmentation")
        self.tabs.addTab(self.tracking_widget, "Tracking")
        self.tabs.addTab(self.property_filter_widget, "Properties Filter")
        # self.tabs.addTab(self.stepanalysis_widget, "Step Analysis")
