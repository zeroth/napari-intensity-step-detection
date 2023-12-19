from qtpy.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QToolButton, QStyle, QHBoxLayout, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QIcon
from napari_intensity_step_detection.main_panel_widget import MainPanel
from pathlib import Path


class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.setLayout(QVBoxLayout())
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)

        self.segmentation_widget = MainPanel(napari_viewer=napari_viewer)
        self.tabs.addTab(self.segmentation_widget, "Main")

        # setup the top left Action Menu
        self.btn_save = QToolButton()
        self.btn_save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_save.setMinimumWidth(20)
        self.btn_save.setMinimumHeight(20)

        def _save_clicked():
            file_path = QFileDialog.getSaveFileName(self,
                                                    caption="Save Track State Project",
                                                    directory=str(Path.home()),
                                                    filter="*.tracks")
            if len(file_path[0]):
                print(file_path)
                self.app_state.save(file_path[0])
        self.btn_save.clicked.connect(_save_clicked)

        self.btn_open = QToolButton()
        self.btn_open.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.btn_open.setMinimumWidth(20)
        self.btn_open.setMinimumHeight(20)

        def _open_clicked():
            file_path = QFileDialog.getOpenFileName(self,
                                                    caption="Open Track State Project",
                                                    directory=str(Path.home()),
                                                    filter="*.tracks")
            if len(file_path[0]):
                print(file_path)
                # self.app_state.open(file_path[0])
                # TODO: open the project
        self.btn_open.clicked.connect(_open_clicked)
        # self.btn_open.clicked.connect(self.app_state.open)

        # left corner
        corner_widget = QWidget()
        corner_widget.setLayout(QHBoxLayout())
        corner_widget.layout().setContentsMargins(0, 0, 0, 0)
        corner_widget.layout().setSpacing(1)
        corner_widget.layout().addWidget(self.btn_save)
        corner_widget.layout().addWidget(self.btn_open)
        corner_widget.setMinimumWidth(41)
        corner_widget.setMinimumHeight(21)
        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopLeftCorner)


def _napari_main():
    import napari
    viewer = napari.Viewer()
    win = PluginWidget(viewer)
    viewer.window.add_dock_widget(win, name="Plugin", area="right")
    napari.run()


if __name__ == "__main__":
    _napari_main()
