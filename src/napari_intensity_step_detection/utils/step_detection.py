import numpy as np
from math import sqrt


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
