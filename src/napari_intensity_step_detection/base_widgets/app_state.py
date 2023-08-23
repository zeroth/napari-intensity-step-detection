from qtpy.QtCore import QObject, Signal
import napari
from napari.utils.events import Event


class AppState(QObject):
    nLayerInserted = Signal(Event)
    nLayerRemoved = Signal(Event)
    parametersUpdated = Signal(str, dict)
    dataUpdated = Signal(str, dict)
    objectUpdated = Signal(str, dict)

    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent=None):
        super(AppState, self).__init__(parent=parent)
        self.viewer = napari_viewer
        self._parameters = dict()
        self._data = dict()
        self._objects = dict()

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

    def hasParameter(self, key):
        return key in self._parameters if self._parameters else False

    def setData(self, name, value):
        self._data[name] = value
        self.dataUpdated.emit(name, {'value': value})

    def data(self, name):
        return self._data.get(name, None)

    def hasData(self, key):
        return key in self._data if self._data else False

    def setObject(self, name, value):
        self._objects[name] = value
        self.objectUpdated.emit(name, {'value': value})

    def object(self, name):
        return self._objects.get(name, None)

    def hasObject(self, key):
        return (key in self._objects) if self._objects else False

    def getLayer(self, name):
        return self.viewer.layers[name]

    def getLayers(self):
        return self.viewer.layers
