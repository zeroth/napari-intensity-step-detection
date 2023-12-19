import numpy as np
from math import sqrt
from skimage.draw import disk, circle_perimeter


def draw_points(image, points, radius=1, fill_value=255, outline_value=0):
    # points = points[:,:2]
    def map_bound(limit):
        def fun(val):
            # logging.info("befor: limit %d. val %d", limit, val)
            if val >= limit:
                val = limit-1
            elif val < 0:
                val = 0
            # logging.info("after: limit %d. val %d", limit, val)
            return val
        return fun

    for y, x, r in points:
        _radius = r*sqrt(2)
        rr, cc = disk((y, x), radius=_radius, shape=image.shape)
        rr = np.array(list(map(map_bound(image.shape[0]), rr)), dtype='uint16')
        cc = np.array(list(map(map_bound(image.shape[1]), cc)), dtype='uint16')
        image[rr, cc] = fill_value
        if outline_value > 0:
            o_rr, o_cc = circle_perimeter(int(y), int(x), radius=int(np.ceil(_radius)), shape=image.shape)
            image[o_rr, o_cc] = outline_value

    return image


def remove_small_objects(img, min_size=10, connectivity=2):
    from skimage import morphology
    # print("img ", img.dtype)
    binary = np.array(img > 0)
    binary = binary.astype(np.bool_)
    # print("binary ", binary)
    # print("binaryd ", binary.dtype)
    bim = morphology.binary_dilation(binary, footprint=np.ones((2, 2)))  # min_size=min_size, connectivity=connectivity
    bim = morphology.binary_opening(bim)
    ret = np.array(bim, dtype=np.uint8)
    # print(ret.dtype)
    # print(ret)
    return ret


def quick_log(image, min_sigma: float = 1.0, max_sigma: float = 2.0,
              num_sigma: int = 10, threshold: float = 0.1, overlap: float = 0.5):
    from skimage.feature import blob_log
    from skimage.exposure import rescale_intensity

    im_range = np.min(image), np.max(image)
    image = rescale_intensity(image, in_range=im_range, out_range=(0, 1))
    blobs_log = blob_log(image, min_sigma=min_sigma, max_sigma=max_sigma,
                         num_sigma=num_sigma, threshold=threshold, overlap=overlap)
    return blobs_log
