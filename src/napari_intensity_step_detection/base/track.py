import numpy as np
import pandas as pd
from napari_intensity_step_detection import utils
from napari_intensity_step_detection.utils import FindSteps


def pd_to_tracks(df: pd.DataFrame):
    tg = df.groupby('track_id', as_index=False, group_keys=True, dropna=True)
    tracks = []
    for track_id, track in tg:
        tracks.append(Track().from_pd(track))


class Track():
    def __init__(self, delta=1, is_3d=False):
        self.is_3d = is_3d
        self.dataframe = None
        self.points = None
        self.frames = None
        self.track_id = None
        self.delta = delta

    def from_pd(self, df):
        if 'frame' not in df.columns:
            raise ValueError("DataFrame does not have frame column")
        if 'track_id' not in df.columns:
            raise ValueError("DataFrame does not have track_id column")

        if not self.is_3d:
            if all(x in df.columns for x in ['x', 'y']):
                raise ValueError("DataFrame does not have x and y column")
        else:
            if all(x in df.columns for x in ['x', 'y', 'z']):
                raise ValueError("DataFrame does not have x, y and z column")

        self.dataframe = df.sort_values(by=['frame'])
        self.points = df[['x', 'y']].to_numpy()
        if self.is_3d:
            self.points = np.concatenate(
                (self.points, df[['z']].to_numpy()), axis=1)

        self.frames = df['frame'].to_numpy()
        self.track_id = df['track_id'].to_numpy()[0]
        _coloumns = list(df.columns)
        _coloumns.remove('x')
        _coloumns.remove('y')
        if self.is_3d:
            _coloumns.remove('z')
        _coloumns.remove('frame')
        _coloumns.remove('track_id')
        # self.properties = df[_coloumns].to_dict()
        # Load additional attributes if provided
        # [setattr(self, attr, value) for attr, value in df[_coloumns].to_dict().items()]
        for col in _coloumns:
            setattr(self, col, df[col].to_numpy())

    def to_pd(self):
        return self.dataframe

    def msd(self, limit=100):
        pos = self.points
        pos_columns = ['x', 'y']
        if self.is_3d:
            pos_columns.append('z')
        result_columns = ['<{}>'.format(p) for p in pos_columns] + \
            ['<{}^2>'.format(p) for p in pos_columns]
        limit = min(limit, len(pos) - 1)
        lagtimes = np.arange(1, limit+1)
        msd_list = []
        for lt in lagtimes:
            diff = pos[lt:] - pos[:-lt]
            msd_list.append(np.concatenate((np.nanmean(diff, axis=0),
                                            np.nanmean(diff**2, axis=0))))
        result = pd.DataFrame(msd_list, columns=result_columns, index=lagtimes)
        result['msd'] = result[result_columns[-len(pos_columns):]].sum(1)
        return result['msd']

    def msd_fit(self):
        return utils.basic_msd_fit(self.msd(), delta=self.delta, limit=100)

    def length(self):
        return len(self.points)

    def velocity(self):
        return self.length() / (self.frames[-1] * self.delta)

    def intensity(self, category='intensity_mean'):
        if not hasattr(self, category):
            return None
        return np.mean(self.intensity)

    def step_detection(self, window=20, threshold=0.5):
        return FindSteps(self.intensity, window=window, threshold=threshold)

    def number_of_steps(self, window=20, threshold=0.5):
        return len(self.step_detection(window=window, threshold=threshold)[0])
