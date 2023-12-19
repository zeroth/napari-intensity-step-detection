import numpy as np


def histogram(data, binsize=5):
    try:
        data = np.array(data).ravel()
        if len(data) > 1:
            data = data[~np.isnan(data)]
        vmin = np.min(data)
        vmax = np.max(data)
        # if abs(vmax - vmin) <= binsize:
        #     binsize = 1 if np.std(data) == 0 else np.std(data)
        if vmin == vmax:
            vmax = vmin+1
        bins = list(np.arange(start=vmin, stop=vmax, step=binsize))
        bins.append(bins[-1]+binsize)
    except Exception as err:
        # print(f"vmin {vmin}, vmax {vmax}, binsize = {binsize}")
        print(f"{err=}, {type(err)=}")
        raise

    hist, edges = np.histogram(data, bins=bins)
    return hist, edges, binsize
