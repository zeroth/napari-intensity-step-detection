import numpy as np
import pandas as pd
import trackpy
from skimage import measure
from tqdm import tqdm


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
