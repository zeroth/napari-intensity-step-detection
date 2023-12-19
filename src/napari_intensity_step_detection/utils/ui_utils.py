from pathlib import Path
from qtpy import uic


def get_icon(name, size=(32, 32)):
    from qtpy.QtGui import QPixmap, QIcon
    from qtpy.QtCore import Qt
    icon_path = str(Path(__file__).parent.parent.resolve().joinpath(
        'ui', 'icons', f'{name}.svg'))
    px = QPixmap(icon_path).scaled(size[0], size[1])
    pxr = QPixmap(px.size())
    pxr.fill(Qt.white)
    pxr.setMask(px.createMaskFromColor(Qt.transparent))
    icon = QIcon(pxr)
    return icon


def load_ui(path, parent):
    uic.loadUi(path, parent)
