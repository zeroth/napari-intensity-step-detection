from pathlib import Path
from qtpy import uic
import pandas as pd
from napari_intensity_step_detection.base_widgets.base_widget import NLayerWidget
from napari_intensity_step_detection.base_widgets.sliders import HFilterSlider
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Signal, QAbstractTableModel, Qt, QModelIndex, QVariant, QObject, QSortFilterProxyModel
import napari


class TrackMetaModel(QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame = pd.DataFrame(),
                 track_id_column_name: str = 'track_id', parent: QObject = None) -> None:
        super().__init__(parent)
        self.beginResetModel()
        self.dataframe = dataframe
        self.endResetModel()
        self.track_id_column_name = track_id_column_name

    def setDataframe(self, dataframe: pd.DataFrame):
        self.beginResetModel()
        self.dataframe = dataframe
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return self.dataframe.shape[0]

    def columnCount(self, parent=QModelIndex()) -> int:
        return self.dataframe.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> QVariant:
        if (not index.isValid()):
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.dataframe.iat[index.row(), index.column()])

        if role == Qt.ItemDataRole.UserRole+1:
            # print("DataFrameModel User Role: ", self.dataframe.iat[index.row(), 0])
            return float(self.dataframe.iat[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> QVariant:
        if role == Qt.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.dataframe.columns[section]
            return str(section)


class TrackMetaModelProxy(QSortFilterProxyModel):
    def __init__(self, parent: QObject = None):
        super(TrackMetaModelProxy, self).__init__(parent)
        self.properties = {}
        self.sourceModelChanged.connect(self.update_prperties)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if (not hasattr(self, 'properties')) or (not self.properties):
            return True
        conditions = []
        for i, (k, v) in enumerate(self.properties.items()):
            if str(k).strip() == self.track_model.track_id_column_name.strip():
                continue
            # print(i, k, v)
            index = self.sourceModel().index(source_row, i+1, source_parent)
            conditions.append((float(self.sourceModel().data(index)) >= v['min'])
                              and (float(self.sourceModel().data(index)) <= v['max']))

        # AND LOGIC
        if all(conditions):
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        return self.sourceModel().headerData(section, orientation, role)

    def setTrackModel(self, model: TrackMetaModel):
        self.track_model = model
        self.setSourceModel(model)

    def update_prperties(self):
        for property in self.track_model.dataframe.columns:
            property = str(property).strip()
            if property == self.track_model.track_id_column_name.strip():
                continue
            _min = self.track_model.dataframe[property].to_numpy().min()
            _max = self.track_model.dataframe[property].to_numpy().max()
            self.properties[property] = {'min': float(_min), 'max': float(_max)}

    def property_filter_updated(self, property_name, vrange):
        print(f"property_filter_updated {property_name}, {vrange}")
        self.properties[property_name] = {'min': vrange[0], 'max': vrange[1]}
        self.invalidateFilter()


class _property_filter_ui(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'filter_view.ui')
        self.load_ui(UI_FILE)

    def load_ui(self, path):
        uic.loadUi(path, self)


class PropertyFilter(NLayerWidget):
    propertyUpdated = Signal(str, tuple)

    def __init__(self, napari_view, parent: QWidget = None):
        super().__init__(napari_view, parent)
        self.ui = _property_filter_ui(self)
        self.layout().addWidget(self.ui)
        self.track_id_column_name = 'track_id'
        self.layer_filter = {"Tracks": napari.layers.Tracks}
        self.setup_ui()

        def _call_setup_ui(event):
            if isinstance(event.value, napari.layers.Tracks):
                self.setup_ui()

        self.layers_hooks.append(_call_setup_ui)

    def setup_ui(self):
        if self.get_current_track() is None:
            return

        track_layer = self.get_current_track()
        track_meta = track_layer.metadata['all_meta']
        track_all_tracks = track_layer.metadata['all_tracks']
        self.model = TrackMetaModel(track_meta, self.track_id_column_name)
        self.all_tracks = track_all_tracks
        self.ui.allView.setModel(self.model)

        self.proxy_model = TrackMetaModelProxy()
        self.proxy_model.setTrackModel(self.model)
        self.ui.filterView.setModel(self.proxy_model)
        self.ui.filterPlots.setModel(self.model)
        self.add_controls(track_meta)
        self.propertyUpdated.connect(self.proxy_model.property_filter_updated)

        # # setup histogram
        # _properties = list(track_meta.columns)
        # _properties.remove(self.track_id_column_name)
        # self.ui.filterProperties.setItems(_properties)

        # def _filter_combo_chnaged():
        #     current_text = self.ui.filterProperties.currentText()
        #     print(current_text)

        # self.ui.filterProperties.currentTextChanged.connect(_filter_combo_chnaged)

    def add_controls(self, track_meta: pd.DataFrame):
        self.ui.filterControls.setLayout(QVBoxLayout())
        self.ui.filterControls.layout().setContentsMargins(0, 0, 0, 0)
        self.ui.filterControls.layout().setSpacing(2)
        for p in track_meta.columns:
            if p == self.track_id_column_name:
                continue
            _slider = HFilterSlider()
            _slider.setTitle(p)
            _p_np = track_meta[p].to_numpy()
            _vrange = (_p_np.min(), _p_np.max())
            _slider.setRange(_vrange)
            _slider.setValue(_vrange)
            _slider.valueChangedTitled.connect(self.propertyUpdated)

            self.ui.filterControls.layout().addWidget(_slider)

    def get_current_track(self):
        return self.get_layer("Tracks")

    def get_current_image_data(self):
        return None if self.get_current_track() is None else self.get_current_track().data
