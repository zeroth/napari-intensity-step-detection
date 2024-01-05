from qtpy.QtWidgets import QWidget, QGridLayout
from .general_plot import GeneralPlot
from napari_intensity_step_detection import utils
import numpy as np


class QuickAnalysisWidget(QWidget):
    def __init__(self, base, parent: QWidget = None):
        super().__init__(parent)
        self.base = base
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.track_plot = GeneralPlot(title="Track", data=None)
        self.msd_plot = GeneralPlot(title="MSD", data=None)
        self.layout().addWidget(self.track_plot, 0, 0)
        self.layout().addWidget(self.msd_plot, 0, 1)

    def set_traget_track_id(self, track_id):
        self.track_id = track_id
        track_layer = self.get_layer('Track')
        if track_layer is None:
            return
        track_df = track_layer.metadata['all_tracks']
        track = track_df[track_df['track_id'] == track_id]
        track = track[['x', 'y']].to_numpy()
        _track = {
            'x_label': 'X',
            'y_label': 'Y',
            'data': {
                'x': track[:, 0],
                'y': track[:, 1],
                'type': 'line'
            }
        }
        self.set_track(_track)

        result = utils.msd(track)
        y = result.to_numpy()
        x = np.arange(0, len(y)) * 5.2
        alfa, _y = utils.basic_msd_fit(y, delta=5.2)
        _msd = {
            'x_label': 'Time (s)',
            'y_label': 'MSD',
            'data': {
                'x': x,
                'y': _y,
                'type': 'line'}
        }
        self.set_msd(_msd)
        # all_alfa[name] = alfa

    def set_track(self, track):
        self.track_plot.setData(data=track)
        self.track_plot.draw()

    def set_msd(self, msd):
        self.msd_plot.setData(data=msd)
        self.msd_plot.draw()
