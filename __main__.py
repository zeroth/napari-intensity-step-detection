# launch_napari.py
from napari import Viewer, run
# import tifffile
from qtpy.uic import compileUi
from pathlib import Path
from pprint import pprint
import logging

# logging.basicConfig(filename="nisd.log",
#                     filemode='a',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.CRITICAL)


def build():
    UI_DIR = Path(__file__).resolve().parent.joinpath(
        'src', 'napari_intensity_step_detection', 'ui')
    UI_FILE = UI_DIR.joinpath("h_slider.ui")
    pyfile_name = f"ui_{UI_FILE.stem}.py"
    pyfile = open(UI_FILE.with_name(pyfile_name), 'wt', encoding='utf8')
    compileUi(UI_FILE, pyfile)  # from_imports=True, import_from='qtpy'
    pprint(pyfile)
    # for uifile in UI_FILES:
    #     pyfile_name = f"ui_{uifile.stem}.py"
    #     pyfile = open(uifile.with_name(pyfile_name), 'wt', encoding='utf8')
    #     compileUi(uifile, pyfile)  # from_imports=True, import_from='qtpy'
    #     pprint(pyfile)


def launch():
    viewer = Viewer()
    dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
        "napari-intensity-step-detection", "Step Detection"
    )
    # viewer.add_image(tifffile.imread("image.tif"))
    # viewer.add_labels(tifffile.imread("mask.tif"))

    run()


if __name__ == "__main__":
    try:
        launch()
    except Exception as e:
        print(e)
        # logging.exception(e)
