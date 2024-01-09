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

    def set_traget_track(self, track):
        self.track = track

        _track = {
            'x_label': 'X',
            'y_label': 'Y',
            'data': {
                'y': track.points[:, 0],
                'x': track.points[:, 1],
                'type': 'line'
            }
        }
        self.set_track(_track)

        y = track.msd
        x = np.arange(0, len(y)) * track.delta
        alfa, _y = track._msd_fit_op
        _msd = {
            'x_label': 'Time (s)',
            'y_label': 'MSD',
            'data': [{
                'x': x,
                'y': _y,
                'type': 'line'},
                {
                'x': x,
                'y': y,
                'type': 'line'}]
        }
        self.set_msd(_msd)
        # all_alfa[name] = alfa

    def set_track(self, track):
        self.track_plot.setData(data=track)
        self.track_plot.draw()

    def set_msd(self, msd):
        self.msd_plot.setData(data=msd)
        self.msd_plot.draw()
