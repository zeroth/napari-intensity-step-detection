from pathlib import Path
from qtpy.QtWidgets import QWidget, QVBoxLayout
import warnings
from napari.utils import notifications
import napari_intensity_step_detection.utils as utils
import numpy as np


class _quick_annotation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.joinpath('quick_annotation_widget.ui')
        utils.load_ui(UI_FILE, self)

        # Blob_Log
        self.minSigmaSpinner.setMinimum(1.0)
        self.minSigmaSpinner.setValue(1.0)
        self.maxSigmaSpinner.setMinimum(1.0)
        self.maxSigmaSpinner.setValue(2.0)
        self.numSigmaSpinner.setMinimum(1)
        self.numSigmaSpinner.setValue(10)
        self.thresholdSpinner.setMinimum(0.0)
        self.thresholdSpinner.setValue(0.1)
        self.overlapSpinner.setMinimum(0.0)
        self.overlapSpinner.setValue(0.5)


class QuickAnnotation(QWidget):
    def __init__(self, base, parent=None):
        super().__init__(parent=parent)
        self.base = base
        self.setLayout(QVBoxLayout())
        self.ui = _quick_annotation(self)
        self.layout().addWidget(self.ui)

        # quick segment button
        def quick_segment_clicked(*arg, **kwargs):
            image_layer = self.base.get_layer("Image")
            if image_layer is None:
                warnings.warn("Please select image!")
                notifications.show_warning(
                    "Please select image!")
                return

            label_layer = self.base.get_layer("Label")
            self.quick_segment_2d(
                image_layer=image_layer,
                label_layer=label_layer,
                min_sigma=self.ui.minSigmaSpinner.value(),
                max_sigma=self.ui.maxSigmaSpinner.value(),
                num_sigma=self.ui.numSigmaSpinner.value(),
                threshold=self.ui.thresholdSpinner.value(),
                overlap=self.ui.overlapSpinner.value()
            )

        self.ui.btnLog.clicked.connect(quick_segment_clicked)

    def quick_segment_2d(self, image_layer, label_layer, min_sigma: float = 1.0, max_sigma: float = 2.0,
                         num_sigma: int = 10, threshold: float = 0.1, overlap: float = 0.5):

        if self.base.napari_viewer.dims.ndisplay != 2:
            warnings.warn("Plese sqitch to 2d Display Mode!")
            notifications.show_warning(
                "Plese sqitch to 2d Display Mode!")
            return
        image = image_layer.data[self.base.napari_viewer.dims.current_step[0]]
        if label_layer is not None:
            label = label_layer.data[self.base.napari_viewer.dims.current_step[0]]
        else:
            label_layer = self.base.napari_viewer.add_labels(
                np.zeros(image_layer.data.shape, dtype=np.uint8),
                name="Annotation_Label")
            label = label_layer.data[self.base.napari_viewer.dims.current_step[0]]

        blobs_log = utils.quick_log(image, min_sigma=min_sigma, max_sigma=max_sigma,
                                    num_sigma=num_sigma, threshold=threshold, overlap=overlap)
        label = utils.draw_points(label, blobs_log, fill_value=2, outline_value=1)
        label_layer.data[self.base.napari_viewer.dims.current_step[0]] = label
        self.base.napari_viewer.reset_view()
