"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from qtpy.QtWidgets import QVBoxLayout, QWidget, QLabel
from qtpy.QtCore import Qt


from .segmentation.segmentation_widget import SegmentationWidget
from .tracking.tracking_widget import TrackingWidget
from .step_analysis.stepanalysis_widget import StepAnalysisWidget


class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.segmentation_widget = SegmentationWidget(napari_viewer)
        self.tracking_widget = TrackingWidget(napari_viewer)
        self.stepanalysis_widget = StepAnalysisWidget()

        self.setLayout(QVBoxLayout())
        
        title = QLabel("<h2><u>Segmentation</u></h2>")
        title.setTextFormat(Qt.TextFormat.RichText)
        self.layout().addWidget(title)
        self.layout().addWidget(self.segmentation_widget)

        title = QLabel("<h2><u>Tracking</u></h2>")
        title.setTextFormat(Qt.TextFormat.RichText)
        self.layout().addWidget(title)
        self.layout().addWidget(self.tracking_widget)

        title = QLabel("<h2><u>Step Analysis</u></h2>")
        title.setTextFormat(Qt.TextFormat.RichText)
        self.layout().addWidget(title)
        self.layout().addWidget(self.stepanalysis_widget)

