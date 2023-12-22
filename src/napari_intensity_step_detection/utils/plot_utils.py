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


def msd_alfa_plot(data, binsize=5):
    bins = np.linspace(start=np.min(data), stop=np.max(data), num=int(len(data)/5))
    hist, edge = np.histogram(data, bins=bins)
    return hist, edge[:-1]


def normalizeData(data, rmin=None, rmax=None, tmin=0, tmax=1):
    """
    /*
            rmin denote the minimum of the range of your measurement
            rmax denote the maximum of the range of your measurement
            tmin denote the minimum of the range of your desired target scaling
            tmax denote the maximum of the range of your desired target scaling
            m ∈ [rmin,rmax] denote your measurement to be scaled

            Then m = ((m - rmin)/ (rmax - rmin)) * (tmax - tmin)+tmin
        */
    """
    rmin = np.min(data) if rmin is None else rmin
    rmax = np.max(data) if rmax is None else rmax
    return ((data - rmin) / (rmax - rmin)) * (tmax - tmin) + tmin
