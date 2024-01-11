from qtpy.QtCore import Qt, QModelIndex, QAbstractTableModel, QVariant, Signal, QObject, QSortFilterProxyModel
from qtpy.QtGui import QStandardItemModel, QStandardItem
import numpy as np
import pandas as pd
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import FindSteps


def pd_to_tracks(df: pd.DataFrame, is_3d=False, delta=1, min_length=5, step_detection=False, ignore_reagion=None, progress=None):
    tg = df.groupby('track_id', as_index=False, group_keys=True, dropna=True)
    tracks = []
    if progress is not None:
        tg = progress(tg, desc="Creating to tracks")
    for track_id, track in tg:
        t = from_pd_track(track, delta=delta, is_3d=is_3d,
                          step_detection=step_detection)
        if t.length < min_length:
            continue
        if ignore_reagion is not None:
            if t.is_in_bbox(ignore_reagion[0], ignore_reagion[1]):
                continue
        tracks.append(t)
    return tracks


def tracks_to_pd(tracks):
    df = pd.concat([t.to_pd() for t in tracks])
    return df


def filter_tracks_by_id(tracks, track_ids):
    return [t for t in tracks if t.track_id in track_ids]


def tracks_to_napari_tracks(tracks, progress=None):
    napari_tracks = None
    properties_columns = tracks[0].properties_columns
    if progress is not None:
        tracks = progress(tracks, desc="Converting tracks to napari tracks")
    for track in tracks:
        if napari_tracks is not None:
            napari_tracks = np.concatenate(
                (napari_tracks, track.napari_points))
        else:
            napari_tracks = track.napari_points
        # napari_tracks.append(track.points)

    properties = {}
    tracks_df = tracks_to_pd(tracks)
    _tracks_df = tracks_df[properties_columns]
    properties = _tracks_df.to_dict()
    properties = dict(
        map(lambda kv: (kv[0], np.array(list(kv[1].values()))), properties.items()))

    return np.array(napari_tracks), properties


def tracks_to_tracks_meta(tracks, progress=None):
    tracks_meta = []
    if progress is not None:
        tracks = progress(tracks, desc="Creating tracks meta data")
    for track in tracks:
        tracks_meta.append(track.meta())

    meta_pd = pd.DataFrame(tracks_meta)
    return meta_pd


def from_pd_track(df, is_3d=False, step_detection=False, delta=1):
    if 'frame' not in df.columns:
        raise ValueError("DataFrame does not have frame column")
    if 'track_id' not in df.columns:
        raise ValueError("DataFrame does not have track_id column")

    if not is_3d:
        if not all(x in df.columns for x in ['x', 'y']):
            raise ValueError("DataFrame does not have x and y column")
    else:
        if not all(x in df.columns for x in ['x', 'y', 'z']):
            raise ValueError("DataFrame does not have x, y and z column")

    t = Track(delta=delta, is_3d=is_3d, is_step_detection=step_detection)
    t.dataframe = df.sort_values(by=['frame'])
    if is_3d:
        t.points = df[['z', 'y', 'x']].to_numpy()
        t.napari_points = df[['track_id', 'frame', 'z', 'y', 'x']].to_numpy()
    else:
        t.points = df[['y', 'x']].to_numpy()
        t.napari_points = df[['track_id', 'frame', 'y', 'x']].to_numpy()

    if t.is_3d:
        t.points = np.concatenate(
            (t.points, df[['z']].to_numpy()), axis=1)

    t.frames = df['frame'].to_numpy()
    t.track_id = df['track_id'].to_numpy()[0]
    _columns = list(df.columns)
    _columns.remove('x')
    _columns.remove('y')
    if t.is_3d:
        _columns.remove('z')
    _columns.remove('frame')
    _columns.remove('track_id')
    t.properties_columns = _columns

    # convert dict of dict to dict of np.array
    # t.properties = dict(
    #     map(lambda kv: (kv[0], np.array(list(kv[1].values()))), _properties.items()))

    # Load additional attributes if provided
    for col in _columns:
        setattr(t, col, df[col].to_numpy())

    t.length = len(t.points)
    t.mean_intensity = np.nanmean(t.intensity())

    return t


class Track():
    def __init__(self, delta=1, is_3d=False, is_step_detection=False):
        self.is_3d = is_3d
        self.dataframe = None
        self.points = None
        self.napari_points = None
        self.frames = None
        self.delta = delta
        self.msd = None
        self.msd_limit = 100
        self.properties = None

        # meta attributes
        self.track_id = None
        self.intensity_mean = None
        self.velocity = None
        self.msd_fit_op = None

    def to_pd(self):
        return self.dataframe

    def set_delta(self, delta):
        if delta == self.delta:
            return
        self.delta = delta
        self.msd = None
        self.msd_fit_op = None

    def calculate_msd(self, limit=100):
        if (self.msd is not None) and (limit <= self.msd_limit):
            return self.msd  # return if already calculated

        self.msd_limit = limit
        pos = self.points
        if len(self.points) < 5:
            return None
        pos_columns = ['x', 'y']
        if self.is_3d:
            pos_columns.append('z')
        result_columns = ['<{}>'.format(p) for p in pos_columns] + \
            ['<{}^2>'.format(p) for p in pos_columns]
        limit = min(limit, len(pos) - 1)
        self.msd_limit = limit
        lagtimes = np.arange(1, limit+1)
        msd_list = []
        for lt in lagtimes:
            diff = pos[lt:] - pos[:-lt]
            msd_list.append(np.concatenate((np.nanmean(diff, axis=0),
                                            np.nanmean(diff**2, axis=0))))
        result = pd.DataFrame(msd_list, columns=result_columns, index=lagtimes)
        result['msd'] = result[result_columns[-len(pos_columns):]].sum(1)
        self.msd = result['msd'].to_numpy()
        return self.msd

    def msd_fit(self):
        if self.msd_fit_op is not None:
            return self.msd_fit_op
        _msd = self.calculate_msd(self.msd_limit)
        if _msd is None:
            return [None, None]
        self.msd_fit_op = utils.basic_msd_fit(
            self.calculate_msd(self.msd_limit), delta=self.delta, limit=self.msd_limit)
        return self.msd_fit_op

    def track_velocity(self):
        return self.length / (self.frames[-1] * self.delta)

    def intensity(self, category='intensity_mean'):
        if not hasattr(self, category):
            return None
        return getattr(self, category)

    def step_detection(self, window=20, threshold=0.5):
        return FindSteps(self.intensity, window=window, threshold=threshold)

    def number_of_steps(self, window=20, threshold=0.5):
        return len(self.step_detection(window=window, threshold=threshold)[0])

    def is_in_bbox(self, top_left, bottom_right):
        if top_left is None or bottom_right is None:
            return True
        point = self.points[0]
        return ((top_left[0] <= point[0] <= bottom_right[0])
                or (top_left[0] >= point[0] >= bottom_right[0])) \
            and ((top_left[1] <= point[1] <= bottom_right[1])
                 or (top_left[1] >= point[1] >= bottom_right[1]))

    def meta(self):
        meta = {}
        meta['track_id'] = self.track_id
        meta['length'] = self.length
        meta['msd_fit_alpha'] = self.msd_fit()[0]
        meta['mean_intensity'] = self.mean_intensity
        # meta['number_of_steps'] = self.number_of_steps()
        return meta

    def __repr__(self) -> str:
        return f"Track(track_id={self.track_id}, length={self.length}"

    def __str__(self) -> str:
        return self.__repr__()


class TrackMetaModel(QStandardItemModel):
    def __init__(self, tracks_meta=pd.DataFrame, track_id_column='track_id', parent=None):
        super().__init__(parent)
        self.track_id_column = track_id_column
        self.tracks_meta = tracks_meta
        self.setHorizontalHeaderLabels(list(self.tracks_meta.columns))
        self.setup()

    def setup(self):
        # numpy data type reference https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind
        types = self.tracks_meta.dtypes.values
        for i, row in self.tracks_meta.iterrows():
            r = []
            for j, v in enumerate(row):
                if types[j].kind == 'f':
                    r.append(QStandardItem("{:.4f}".format(v)))
                elif types[j].kind == 'i' or types[j].kind == 'u':
                    r.append(QStandardItem(str(int(v))))
                else:
                    r.append(QStandardItem(str(v)))
            self.appendRow(r)
            # self.appendRow([QStandardItem(str(v)) for v in row])


class TrackMetaProxyModel(QSortFilterProxyModel):
    def __init__(self,  parent: QObject = None):
        super(TrackMetaProxyModel, self).__init__(parent)
        self.properties = {}
        self.sourceModelChanged.connect(self.setup_prperties)
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if (not hasattr(self, 'properties')) or (not self.properties):
            return True
        conditions = []
        for i, (k, v) in enumerate(self.properties.items()):
            if str(k).strip() == self.tracks_meta_model.track_id_column.strip():
                continue
            # print(i, k, v)
            index = self.sourceModel().index(source_row, i+1, source_parent)
            conditions.append((float(self.sourceModel().data(index)) >= v['min'])
                              and (float(self.sourceModel().data(index)) <= v['max']))

        # AND LOGIC
        if all(conditions):
            return True
        return False

    def lessThan(self, source_left, source_right):
        leftData = self.sourceModel().data(source_left)
        rightData = self.sourceModel().data(source_right)
        return float(leftData) < float(rightData)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        return self.sourceModel().headerData(section, orientation, role)

    def setTrackMetaModel(self, model: TrackMetaModel):
        self.tracks_meta_model = model
        self.setSourceModel(model)

    def setup_prperties(self):
        for property in self.tracks_meta_model.tracks_meta.columns:
            property = str(property).strip()
            if property == self.tracks_meta_model.track_id_column.strip():
                continue
            _min = self.tracks_meta_model.tracks_meta[property].to_numpy(
            ).min()
            _max = self.tracks_meta_model.tracks_meta[property].to_numpy(
            ).max()
            self.properties[property] = {
                'min': float(_min), 'max': float(_max)}

    def property_filter_updated(self, property_name, vrange):
        print(f"property_filter_updated {property_name}, {vrange}")
        self.properties[property_name] = {'min': vrange[0], 'max': vrange[1]}
        # self.filterUpdated.emit(property_name, vrange)
        self.invalidateFilter()
