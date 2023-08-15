# launch_napari.py
from napari import Viewer, run
import tifffile

viewer = Viewer()
dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "napari-intensity-step-detection", "Step Detection"
)
viewer.add_image(tifffile.imread(
    "D:\\Data\\tracking_test\\DYNC1H1_photobleaching\\HaloDYN_230314_1003_200.tif"))
viewer.add_labels(tifffile.imread(
    "D:\\Data\\tracking_test\\DYNC1H1_photobleaching\\HaloDYN_230314_1003_200_mask.tif"))
run()
