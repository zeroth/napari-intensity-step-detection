import typing
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
import napari
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget, QFormLayout, QComboBox, QVBoxLayout, QLabel


class NLayerWidget(QWidget):
    def __init__(self, napari_viewer: napari.viewer.Viewer = None, parent: QWidget = None):
        super().__init__(parent)
        self.viewer = napari_viewer
        self.layers_combo_container = {}
        self.layer_filter = {"Image": napari.layers.Image,
                             "Label": napari.layers.Labels}
        self.cmb_form_layout = QFormLayout()
        self.main_layout = QVBoxLayout()
        self.msg_label = QLabel("Open Image and Label to get started")
        self.main_layout.addWidget(self.msg_label)
        self.main_layout.addLayout(self.cmb_form_layout)
        self.setLayout(self.main_layout)

        if self.viewer:
            self.viewer.layers.events.inserted.connect(
                self.viewer_layer_updated)
            self.viewer.layers.events.removed.connect(
                self.viewer_layer_updated)

    def viewer_layer_updated(self, event):
        for name, dtype in self.layer_filter.items():
            if isinstance(event.value, dtype):
                self.update_combo(name, dtype)

    def update_combo(self, name, dtype, is_internal=False):
        combo_box = self.layers_combo_container.get(name, QComboBox())
        combo_box.clear()
        for i, l in enumerate(self.viewer.layers):
            if isinstance(l, dtype):
                combo_box.addItem(l.name, i)

        if combo_box.count() == 0:  # All the layer of dtype has been removed
            self.cmb_form_layout.removeRow(combo_box)
            del combo_box
            del self.layers_combo_container[name]
            return

        if not (name in self.layers_combo_container):
            self.cmb_form_layout.addRow(name, combo_box)
            self.layers_combo_container[name] = combo_box

        if self.cmb_form_layout.rowCount():
            self.msg_label.setVisible(False)
        else:
            self.msg_label.setVisible(True)

    def get_layer(self, name):
        combo = self.layers_combo_container.get(name, None)
        if combo is None:
            return None
        return self.viewer.layers[combo.currentText()]

    def get_layer_name(self, name):
        combo = self.layers_combo_container.get(name, None)
        if combo is None:
            return None
        return combo.currentText()
