<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
from napari_intensity_step_detection.base_widgets import NLayerWidget, AppState, MultiHistogramWidgets
from napari_intensity_step_detection.filter_widget import PropertyFilter
from qtpy.QtWidgets import QWidget, QVBoxLayout
=======
from napari_intensity_step_detection.base import NLayerWidget, AppState
from napari_intensity_step_detection.filter_widget import FilterWidget
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFileDialog
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py
from qtpy.QtCore import Qt
from qtpy.QtGui import QIntValidator
from qtpy import uic
from pathlib import Path
from napari_intensity_step_detection import utils
import pandas as pd
from napari.utils import progress
import numpy as np


<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
=======
class ResultWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'step_analysis_result_widget.ui')
        self.load_ui(UI_FILE)
        self.btnExport.setIcon(utils.get_icon('file-export'))
        self.data = data
        self.setup_ui()

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setup_ui(self):
        step_meta: pd.DataFrame = self.data['steps_meta_df']
        data_dict = {}
        data_dict['step_count'] = step_meta['step_count'].to_numpy()
        data_dict['negetive_vs_positive'] = np.hstack([step_meta['negetive_steps'].to_numpy(),
                                                       step_meta['positive_steps'].to_numpy()])
        data_dict['single_step_height'] = np.abs(
            (step_meta[step_meta['step_count'] == 1]['step_height']).to_numpy())
        data_dict['max_intensity'] = step_meta['max_intensity'].to_numpy()
        data_dict['step_height'] = np.abs((self.data['steps_df']['step_height']).to_numpy())
        data_dict['track_length'] = step_meta['length'].to_numpy()
        self.histogram.setData(data=data_dict)
        self.btnExport.clicked.connect(self.export)

    def export(self):
        file_path = QFileDialog.getSaveFileName(self,
                                                caption="Export step analysis results in csv",
                                                directory=str(Path.home()),
                                                filter="*.csv")
        if not len(file_path[0]):
            return

        print(file_path)
        df = self.data['steps_df']
        df.to_csv(file_path[0])


>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py
class _step_analysis_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'step_analysis_widget.ui')
        self.load_ui(UI_FILE)
        self.leWindowSize.setValidator(QIntValidator())

    def load_ui(self, path):
        uic.loadUi(path, self)


class StepAnalysisWidget(NLayerWidget):
    def __init__(self, app_state: AppState = None, parent=None):
        super().__init__(app_state=app_state, parent=parent)
        self.ui = _step_analysis_ui(self)
        self.layout().addWidget(self.ui)
        self.gbNapariLayers.setVisible(False)
<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py

        self.property_widget = PropertyFilter(self.state, parent=self)
=======
        self.ui.resultWidget.clear()

        self.property_widget = FilterWidget(self.state, parent=self)

        def _call_setup_ui(key, val):
            if key == "tracking_model":
                print("_call_setup_ui")
                self.property_widget.setup_ui()
        self.state.objectAdded.connect(_call_setup_ui)
        self.state.objectUpdated.connect(_call_setup_ui)

>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py
        self.ui.filterTable.setLayout(QVBoxLayout())
        self.ui.filterTable.layout().addWidget(self.property_widget)

        self.property_widget.gbFilterControls.setVisible(False)
        self.property_widget.gbHistogram.setVisible(False)
        self.property_widget.tabWidget.setTabVisible(1, False)
        self.property_widget.proxySelectionChanged.connect(self.track_selected)
<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
        self.ui.resultWidget.setDocumentMode(True)
=======
        # self.ui.resultWidget.setDocumentMode(True)
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py

        def _reDrawPlot():
            if hasattr(self, "current_track"):
                self.track_selected(self.current_track)

        self.ui.sbThreshold.valueChanged.connect(_reDrawPlot)
        self.ui.leWindowSize.editingFinished.connect(_reDrawPlot)
        self.ui.fitAll.clicked.connect(self.apply_all)

        def _render_results(key, val):
            if key == 'stepanalysis_result':
                self.render_plots()
        self.state.dataAdded.connect(_render_results)
        self.state.dataUpdated.connect(_render_results)

        def _toggle_oriantation():
            if (self.ui.splitter.orientation() == Qt.Orientation.Horizontal):
                self.ui.splitter.setOrientation(Qt.Orientation.Vertical)
            else:
                self.ui.splitter.setOrientation(Qt.Orientation.Horizontal)

<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
        self.ui.btnOriantation.clicked.connect(_toggle_oriantation)

    def track_selected(self, track_id):
        self.current_track = track_id
        tracks_df = self.state.data("tracking_df")
        all_tracks = tracks_df['tracks']
        if 'intensity_mean' in all_tracks.columns:
            track = all_tracks[all_tracks['track_id'] == track_id]
            intensity = track['intensity_mean'].to_numpy()
            _, fitx, _ = utils.FindSteps(data=intensity,
                                         window=int(self.ui.leWindowSize.text()),
                                         threshold=self.ui.sbThreshold.value())
        self.ui.intensityPlot.draw(intensity, fitx, f"Track {track_id}")
=======
        self.state.toggleOriantation.connect(_toggle_oriantation)

    def track_selected(self, track_id):
        print(f"track_selected {track_id}")
        self.current_track = track_id
        tracks_df = self.state.data("tracking")
        all_tracks = tracks_df['tracks_df']
        if 'intensity_mean' in all_tracks.columns:
            track = all_tracks[all_tracks['track_id'] == track_id]
            intensity = track['intensity_mean'].to_numpy()
            if len(intensity) < 5:
                self.ui.intensityPlot.draw(intensity, [], f"Track {track_id}")
                return
            _, fitx, _ = utils.FindSteps(data=intensity,
                                         window=int(self.ui.leWindowSize.text()),
                                         threshold=self.ui.sbThreshold.value())
            self.ui.intensityPlot.draw(intensity, fitx, f"Track {track_id}")
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py

    def apply_all(self):
        print("Step fitting started")
        models = self.state.object("tracking_model")
        proxy_model = models['proxy']

<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
        dfs = self.state.data("tracking_df")
        all_tracks = dfs['tracks']
=======
        dfs = self.state.data("tracking")
        all_tracks = dfs['tracks_df']
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py
        step_meta = []
        steps_info = pd.DataFrame()
        rows = proxy_model.rowCount()
        window = int(self.ui.leWindowSize.text())
        threshold = self.ui.sbThreshold.value()
        print(f"Total number of rows {rows}")

        for row in progress(range(rows), desc="Analysing steps.."):
            index = proxy_model.index(row, 0, self.property_widget.filterView.rootIndex())
            track_id = int(proxy_model.data(index))
            track = all_tracks[all_tracks['track_id'] == track_id]
            intensity = track['intensity_mean'].to_numpy()
            steptable, fitx, _ = utils.FindSteps(data=intensity,
                                                 window=window,
                                                 threshold=threshold)

            # all_tracks.loc[all_tracks['track_id'] == track_id, 'fit'] = fitx
            # Detail step table
            steps_df = pd.DataFrame(steptable,
                                    columns=["step_index", "level_before", "level_after",
                                             "step_height", "dwell_before", "dwell_after", "measured_error"])
            steps_df['track_id'] = track_id
            steps_info = pd.concat([steps_info, steps_df], ignore_index=True)

            # single row description of step table
            meta_row = []
            # track id
            meta_row.append(track_id)
            # number of steps
            meta_row.append(len(steptable))
            # Negetive steps (steps going down)
            meta_row.append(-len(steps_df[steps_df['step_height'] < 0]))
            # Positive steps (steps going up or straight line)
            meta_row.append(len(steps_df[steps_df['step_height'] >= 0]))
            # Average step height
            meta_row.append(steps_df['step_height'].mean())
            # Max Intensity
            meta_row.append(np.max(intensity.ravel()))
            # Track length
            meta_row.append(len(intensity.ravel()))

            step_meta.append(meta_row)

        print("\n\rStep fitting done")

        step_meta_df = pd.DataFrame(data=step_meta,
                                    columns=['track_id', 'step_count', 'negetive_steps',
                                             'positive_steps', 'step_height', 'max_intensity', 'length'])
<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
        _result = {'steps': steps_info,
                   'steps_meta': step_meta_df,
=======
        _result = {'steps_df': steps_info,
                   'steps_meta_df': step_meta_df,
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py
                   'track_filter': proxy_model.properties,
                   'parameters': {'window': window, 'threshold': threshold}}
        result_title = f"{window}_{threshold}_1"
        result = {}
        if self.state.hasData('stepanalysis_result'):
            sr = self.state.data('stepanalysis_result')
            print("total current results ", len(sr.keys()))
            print(f"\t {sr.keys()}")
            result_title = f"{window}_{threshold:.3f}_{len(sr.keys())+1}"
            result = sr

        result[result_title] = _result
        self.state.setData("stepanalysis_result", result)

        # steps_info.to_csv('step_info.csv')
        # step_meta_df.to_csv('step_meta.csv')

    def render_plots(self):
        # ['track_id', 'step_count', 'negetive_steps','positive_steps', 'step_height', 'max_intensity']
        result_obj = self.state.data("stepanalysis_result")

        # TODO check if the tab exist
        results = list(result_obj.keys())
        current_tabs = []
        for i in range(self.ui.resultWidget.count()):
            tab_title = self.ui.resultWidget.tabText(i)
            current_tabs.append(tab_title)

<<<<<<< HEAD:src/napari_intensity_step_detection/step_analysis_widget/stepanalysis_widget.py
        # new_tab = results[0]
        new_tab = list(set(results) - set(current_tabs))[0]
        # if len(current_tabs):
        #     for r in results:
        #         if r not in current_tabs:
        #             new_tab = r
        #             break

        stepanalysis_data = result_obj[new_tab]
        step_meta: pd.DataFrame = stepanalysis_data['steps_meta']
        data_dict = {}
        data_dict['step_count'] = step_meta['step_count'].to_numpy()
        data_dict['negetive_vs_positive'] = np.hstack([step_meta['negetive_steps'].to_numpy(),
                                                       step_meta['positive_steps'].to_numpy()])
        data_dict['single_step_height'] = np.abs((step_meta[step_meta['step_count'] == 1]['step_height']).to_numpy())
        data_dict['max_intensity'] = step_meta['max_intensity'].to_numpy()
        data_dict['step_height'] = np.abs((stepanalysis_data['steps']['step_height']).to_numpy())
        data_dict['track_length'] = step_meta['length'].to_numpy()
        # for c in step_meta.columns:
        #     if c == "track_id":
        #         continue

        #     data_dict[c] = step_meta[c].to_numpy()

        histogram = MultiHistogramWidgets()
        histogram.add_multiple_axes(len(data_dict))
        histogram.draw(data=data_dict)
        self.ui.resultWidget.addTab(histogram, new_tab)
=======
        new_tabs = list(set(results) - set(current_tabs))
        for new_tab in new_tabs:
            stepanalysis_data = result_obj[new_tab]
            resutl_widget = ResultWidget(data=stepanalysis_data)
            self.ui.resultWidget.addTab(resutl_widget, f"Results {new_tab}")


def _qt_main():
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = QWidget()
    # widget.setIcon(utils.get_icon('file-export'))
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _qt_main()
>>>>>>> dev:src/napari_intensity_step_detection/step_analysis_widget/step_analysis_widget.py