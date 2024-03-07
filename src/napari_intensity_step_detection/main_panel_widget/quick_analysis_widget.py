from qtpy.QtWidgets import QWidget, QGridLayout
from qtpy.QtCore import Qt, Signal
from .general_plot import GeneralPlot, StepDetectionPlot
from napari_intensity_step_detection import utils
import numpy as np


class QuickAnalysisWidget(QWidget):
    generateSteps = Signal(float, int)

    def __init__(self, base, parent: QWidget = None):
        super().__init__(parent)
        self.base = base
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.track_plot = GeneralPlot(title="Track", data=None)
        self.msd_plot = GeneralPlot(title="MSD", data=None)
        self.intensity_plot = GeneralPlot(title="Intensity", data=None)
        self.step_detection_plot = StepDetectionPlot(title="Step Detection")
        self.step_detection_plot.createSteps.connect(self.generateSteps)

        self.pos_vs_time = GeneralPlot(title="Position vs Time", data=None)

        self.layout().addWidget(self.track_plot, 0, 0)
        self.layout().addWidget(self.msd_plot, 0, 1)
        self.layout().addWidget(self.intensity_plot, 1, 0)
        self.layout().addWidget(self.step_detection_plot, 1, 1)
        self.layout().addWidget(self.pos_vs_time, 2, 0, 1, 2)

    def set_traget_track(self, track):
        self.track = track

        _track = {
            'x_label': 'X',
            'y_label': 'Y',
            'title': f'Track: {str(track.track_id)} - Track Plot (X, Y)',
            'data': {
                'y': track.points[:, 0],
                'x': track.points[:, 1],
                'type': 'line'
            }
        }
        self.set_track(_track)

        y = track.msd
        x = np.arange(0, len(y)) * track.delta
        alpha, _y = track.msd_fit_op

        _msd = {
            'x_label': 'Time (s)',
            'y_label': 'MSD',
            'title': f'Track: {str(track.track_id)} - MSD fit α: {alpha:.5f}/s',
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

        y = track.intensity()
        x = np.arange(0, len(y)) * track.delta

        print("intensity length", len(x), len(y))

        _intensity = {
            'x_label': 'Time (s)',
            'y_label': 'Intensity',
            'title': f'Track: {str(track.track_id)} - Time vs Intensity',
            'data': {
                'x': x,
                'y': y,
                'type': 'line'
            }
        }
        self.set_intensity(_intensity)

        self.set_steps(track)

        _pos_vs_time = {
            'x_label': 'Time (s)',
            'y_label': 'Position',
            'title': f'Track: {str(track.track_id)} - Position vs Time',
            'data': {
                'x': x,
                'y': track.position_to_displacement(),
                'type': 'line'
            }
        }
        self.set_pos_vs_time(_pos_vs_time)

    def set_track(self, track):
        self.track_plot.setData(data=track)
        self.track_plot.draw()

    def set_msd(self, msd):
        self.msd_plot.setData(data=msd)
        self.msd_plot.draw()

    def set_intensity(self, intensity):
        self.intensity_plot.setData(data=intensity)
        self.intensity_plot.draw()

    def set_steps(self, track):
        self.step_detection_plot.set_track(track)
        self.step_detection_plot.draw_track()

    def set_pos_vs_time(self, _pos_vs_time):
        self.pos_vs_time.setData(_pos_vs_time)
        self.pos_vs_time.draw()
