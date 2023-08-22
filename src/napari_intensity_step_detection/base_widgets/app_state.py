from qtpy.QtCore import QObject, Signal
import napari
from typing import Any
from napari.utils.events import Event


class AppState(QObject):
    nLayerInserted = Signal(Event)
    nLayerRemoved = Signal(Event)
    parametersUpdated = Signal(str, dict)
    dataUpdated = Signal(str, dict)

    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent=None):
        super(AppState, self).__init__(parent=parent)
        self.viewer = napari_viewer
        self._parameters: dict = None
        self._data: dict = None

        if self.viewer:
            def _inserted(event):
                self.nLayerInserted.emit(event)
            self.viewer.layers.events.inserted.connect(_inserted)

            def _removed(event):
                self.nLayerRemoved.emit(event)
            self.viewer.layers.events.removed.connect(_removed)

    def setParameter(self, name, value):
        self._parameters[name] = value
        self.parametersUpdated.emit(name, {'value': value})

    def parameter(self, name):
        return self._parameters.get(name, None)

    def setData(self, name, value):
        self._data[name] = value
        self.dataUpdated.emit(name, {'value': value})

    def data(self, name):
        return self._data.get(name, None)

    def getLayer(self, name):
        return self.viewer.layers[name]

    def getLayers(self):
        return self.viewer.layers
