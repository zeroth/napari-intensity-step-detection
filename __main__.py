# launch_napari.py
from napari import Viewer, run
import tifffile

viewer = Viewer()
dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "napari-intensity-step-detection", "Step Detection"
)
viewer.add_image(tifffile.imread("image.tif"))
viewer.add_labels(tifffile.imread("mask.tif"))

run()
