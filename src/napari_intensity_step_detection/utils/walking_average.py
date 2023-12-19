import numpy as np


def walking_average(self, image, window: int = 4):
    ret = np.cumsum(image, axis=0, dtype=image.dtype)
    ret[window:] = ret[window:] - ret[:-window]
    ret = ret[window - 1:] / window
    return ret
