from qtpy.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QMenu, QAction, QMenuBar
from qtpy.QtCore import Qt
from .segmentation_widget import SegmentationWidget
from .tracking_widget import TrackingWidget
from .filter_widget import PropertyFilterWidget
from .base_widgets import AppState
from .step_analysis_widget import StepAnalysisWidget
import napari


class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.app_state = AppState(napari_viewer=napari_viewer)
        self.setLayout(QVBoxLayout())
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)

        self.segmentation_widget = SegmentationWidget(app_state=self.app_state)
        self.tabs.addTab(self.segmentation_widget, "Segmentation")

        self.tracking_widget = TrackingWidget(app_state=self.app_state)
        self.property_filter_widget = PropertyFilterWidget(app_state=self.app_state)
        self.stepanalysis_widget = StepAnalysisWidget(app_state=self.app_state)
        self.tabs.addTab(self.tracking_widget, "Tracking")
        self.tabs.addTab(self.property_filter_widget, "Properties Filter")
        self.tabs.addTab(self.stepanalysis_widget, "Step Analysis")

        self.tabs.setTabVisible(1, False)
        self.tabs.setTabVisible(2, False)
        self.tabs.setTabVisible(3, False)

        def _track_layer_added(event):
            if isinstance(event.value, napari.layers.Tracks):
                if hasattr(event.value, 'metadata') and ('all_meta' in event.value.metadata):
                    self._track_added()

        self.app_state.nLayerInserted.connect(_track_layer_added)

        # setup the top left Action Menu
        self.menu_bar = QMenuBar(self)
        file_menu = self.menu_bar.addMenu("File")
        _save_act = QAction("save", self)
        file_menu.triggered.connect(lambda x: print("save clicked"))
        file_menu.addAction(_save_act)
        self.tabs.setCornerWidget(self.menu_bar, Qt.Corner.TopLeftCorner)

    def _track_added(self):
        self.tabs.setTabVisible(1, True)
        self.tabs.setTabVisible(2, True)
        self.tabs.setTabVisible(3, True)
