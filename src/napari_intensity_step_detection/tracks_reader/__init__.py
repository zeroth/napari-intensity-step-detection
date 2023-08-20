import gzip
import json
from typing import List
import pandas as pd
from napari_intensity_step_detection import utils


def get_reader(path: str) -> List[str]:
    """
    DataType = Any  # usually something like a numpy array, but varies by layer
    LayerAttributes = dict
    SingleWriterFunction = Callable[[str, DataType, LayerAttributes], List[str]]
    """
    # If we recognize the format, we return the actual reader function
    if isinstance(path, str) and path.endswith(".tracks"):
        return track_stats_reader
    # otherwise we return None.
    return None


def track_stats_reader(path: str):
    with gzip.open(path, 'rb') as f:
        output_gz = f.read()
        output = output_gz.decode('utf-8')
        output = json.loads(output)

    print(output.keys())
    all_tracks = output["all_tracks"]
    all_meta = output["all_meta"]
    tracking_params = output["tracking_params"]
    metadata = {
        "all_tracks": pd.read_json(all_tracks),
        "all_meta": pd.read_json(all_meta),
        "tracking_params": tracking_params
    }
    attributes = output["napari_tracks_properties"]
    print(attributes.keys())
    attributes["metadata"] = metadata
    track_header = ['track_id', 'frame', 'y', 'x']
    track_meta_header = ['track_id', 'length',
                         'intensity_max', 'intensity_mean', 'intensity_min']

    tracks, properties, track_meta = utils.pd_to_napari_tracks(all_tracks,
                                                               track_header,
                                                               track_meta_header)
    attributes["properties"] = properties

    return (tracks, attributes, 'tracks')
