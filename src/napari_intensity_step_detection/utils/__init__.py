import numpy as np
import pandas as pd
import trackpy
from skimage import measure
from tqdm import tqdm
import napari
import warnings
from math import sqrt


class TrackLabels:
    tracks_layer = "All Tracks"
    tracks_meta = "tracks_meta_data"
    tracking_params = "tracking_params"
    track_id = "track_id"
    track_header = ['track_id', 'frame', 'y', 'x']
    track_meta_header = ['track_id', 'length',
                         'intensity_max', 'intensity_mean', 'intensity_min']
    track_table_header = ['label', 'y', 'x', 'intensity_mean',
                          'intensity_max', 'intensity_min', 'area', 'frame', 'track_id']


def get_frame_position_properties(frame: int, mask: np.ndarray, image: np.ndarray = None, result: pd.DataFrame = None,
                                  generate_label: bool = True) -> pd.DataFrame:
    mask_label = measure.label(mask) if generate_label else mask
    properties_keys = ['label', 'centroid', 'intensity_mean',
                       'intensity_max', 'intensity_min', 'area']
    properties = measure.regionprops_table(
        label_image=mask_label, intensity_image=image, properties=properties_keys)
    pf = pd.DataFrame(properties)
    pf['frame'] = frame

    if result is None:
        result = pf
    else:
        result = pd.concat([result, pf], ignore_index=True)

    return result


def get_statck_properties(masks: np.ndarray, images: np.ndarray, result: pd.DataFrame = None,
                          generate_label: bool = True, show_progress=False) -> pd.DataFrame:
    assert images.shape == masks.shape

    iter_range = tqdm(range(images.shape[0])) if show_progress else range(
        images.shape[0])

    for i in iter_range:
        image = images[i]
        mask = masks[i]
        result = get_frame_position_properties(
            frame=i, mask=mask, image=image, result=result, generate_label=generate_label)
    result.rename(columns={'centroid-0': 'y',
                  'centroid-1': 'x'}, inplace=True)
    return result


def get_tracks(df: pd.DataFrame, search_range: float = 2, memory: int = 0, show_progress: bool = False) -> pd.DataFrame:
    trackpy.quiet((not show_progress))
    return trackpy.link(f=df, search_range=search_range, memory=memory)


def napari_track_to_pd(track_layer: napari.layers.Tracks, track_header: list, track_id):
    """
    This function converts the napari Tracks layer to pandas DataFrame

    params:
        track_layer: napari.layers.Tracks

    returns:
        df: pd.DataFrame

    also see:
        pd_to_napari_tracks
    """
    df = pd.DataFrame(track_layer.data, columns=track_header)
    if not hasattr(track_layer, 'properties'):
        warnings.warn(
            "Track layer does not have properties produsing tracking without properties")
        return df

    properties = track_layer.properties
    for property, values in properties.items():
        if property == track_id:
            continue
        df[property] = values
    return df


def pd_to_napari_tracks(df: pd.DataFrame, track_header, track_meta_header):
    """
    This function converts pandas DataFrame to napari Tracks layer paramters
    params:
        df: pandas.DataFrame

    return:
        tracks: np.Array 2D [
            [track_id, time, (c), (z), y, x]
        ]
        properties: dict
        track_meta: pd.DataFrame
    also see:
        napari_track_to_pd
    """
    # assuming df is the dataframe with 'particle' as track_id
    tracks = []
    properties = {}

    columns = list(df.columns)

    for th in track_header:
        columns.remove(th)

    tg = df.groupby('track_id', as_index=False,
                    group_keys=True, dropna=True)
    track_meta = pd.concat([tg['frame'].count(),
                            tg['intensity_mean'].max()['intensity_mean'],
                            tg['intensity_mean'].mean()['intensity_mean'],
                            tg['intensity_mean'].min()['intensity_mean']], axis=1)
    track_meta.columns = track_meta_header

    properties = df[columns].to_dict()
    properties = dict(
        map(lambda kv: (kv[0], np.array(list(kv[1].values()))), properties.items()))

    tracks = df[track_header].to_numpy()

    return tracks, properties, track_meta


def FindSteps(data, window=20, threshold=0.5):
    from scipy.ndimage import gaussian_filter1d
    # filter and normalise the data
    gaussian_data = gaussian_filter1d(data, window, order=1)
    gaussian_normalise = gaussian_data/np.abs(gaussian_data).max()

    # find steps
    indices = []
    gaussian_normalise = np.abs(gaussian_normalise)
    peaks = np.where(gaussian_normalise > threshold, 1, 0)
    peaks_dif = np.diff(peaks)
    ups = np.where(peaks_dif == 1)[0]
    dns = np.where(peaks_dif == -1)[0]
    for u, d in zip(ups, dns):
        g_slice = gaussian_normalise[u:d]
        if not len(g_slice):
            continue
        loc = np.argmax(g_slice)
        indices.append(loc + u)

    last = len(indices) - 1
    table = []
    fitx = np.zeros(data.shape)
    for i, index in enumerate(indices):
        if i == 0:
            level_before = data[0:index]
            if i == last:
                level_after = data[index:]
                dwell_after = len(data) - index
                fitx[index:] = level_after.mean()
            else:
                level_after = data[index:indices[i+1]]
                dwell_after = indices[i+1] - index
                fitx[index:indices[i+1]] = level_after.mean()
            dwell_before = index

            fitx[0:index] = level_before.mean()

        elif i == last:
            level_before = data[indices[i-1]:index]
            level_after = data[index:]
            dwell_before = index - indices[i-1]
            dwell_after = len(data) - index

            fitx[indices[i-1]:index] = level_before.mean()
            fitx[index:] = level_after.mean()
        else:
            level_before = data[indices[i-1]:index]
            level_after = data[index:indices[i+1]]
            dwell_before = index - indices[i-1]
            dwell_after = indices[i+1] - index

            fitx[indices[i-1]:index] = level_before.mean()
            fitx[index:indices[i+1]] = level_after.mean()

        step_error = sqrt(level_after.var() + level_before.var())
        step_height = level_after.mean() - level_before.mean()
        table.append([index, level_before.mean(), level_after.mean(),
                      step_height, dwell_before, dwell_after, step_error])

    return table, fitx, gaussian_normalise


def histogram(data, binsize=5):
    data = np.array(data).ravel()
    vmin = np.min(data)
    vmax = np.max(data)
    bins = list(np.arange(start=vmin, stop=vmax, step=binsize))
    bins.append(bins[-1]+binsize)

    hist, edges = np.histogram(data, bins=bins)
    return hist, edges


def add_track_to_viewer(viewer, name, data, properties=None, scale=None, metadata=None):
    try:
        viewer.layers[name].data = data
        viewer.layers[name].visible = True

        if properties is not None:
            viewer.layers[name].properties = properties
        if metadata is not None:
            viewer.layers[name].metadata = metadata
    except KeyError:
        viewer.add_tracks(data, name=name, properties=properties,
                          scale=scale, metadata=metadata)
