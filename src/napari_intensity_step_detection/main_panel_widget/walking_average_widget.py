from pathlib import Path
from qtpy.QtWidgets import QWidget, QVBoxLayout
import warnings
from napari.utils import notifications
import napari_intensity_step_detection.utils as utils


class _walking_average_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.joinpath('walking_average_widget.ui')
        utils.load_ui(UI_FILE, self)
        self.windowSizeSpinner.setMinimum(1)
        self.windowSizeSpinner.setValue(4)


class WalkingAverage(QWidget):
    def __init__(self, base, parent=None):
        super().__init__(parent=parent)
        self.base = base
        self.setLayout(QVBoxLayout())
        self.ui = _walking_average_ui(self)
        self.layout().addWidget(self.ui)

        # walking average button
        def roalling_average_clicked(*arg, **kwargs):
            if self.base.get_layer("Image") is None:
                warnings.warn("Please select image!")
                notifications.show_warning(
                    "Please select image!")
                return

            image_layer = self.base.get_layer("Image")
            window = self.ui.windowSizeSpinner.value()
            avg_img = utils.walking_average(
                image=image_layer.data,
                window=window
            )

            utils.add_to_viewer(self.state.viewer,
                                f"{image_layer.name}_Walking_Avg_{window}", avg_img, "image", scale=image_layer.scale)

        self.ui.btnAvg.clicked.connect(roalling_average_clicked)
