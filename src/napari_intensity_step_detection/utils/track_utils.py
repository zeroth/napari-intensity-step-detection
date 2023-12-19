import numpy as np
import pandas as pd
import trackpy
from skimage import measure
from tqdm import tqdm
import napari
import warnings


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
