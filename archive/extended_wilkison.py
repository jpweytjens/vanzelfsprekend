def floored_mod(a, n):
    """
    Compute the floored modulus of `a` by `n`.

    Parameters
    ----------
    a : float
        The dividend.
    n : float
        The divisor.

    Returns
    -------
    float
        The remainder of the floored division.
    """
    return a - n * np.floor(a / n)


def simplicity(q, Q, j, lmin, lmax, lstep):
    """
    Calculate the simplicity of a proposed labeling scheme based on the given parameters.

    Parameters
    ----------
    q : float
        The label step being used.
    Q : array-like
        The set of nice numbers for label steps.
    j : int
        The power of 10 scaling factor applied to the label step.
    lmin : float
        The minimum label value in the labeling scheme.
    lmax : float
        The maximum label value in the labeling scheme.
    lstep : float
        The step between labels in the labeling scheme.

    Returns
    -------
    float
        The simplicity score for the given labeling scheme.
    """
    eps = 1e-10
    n = len(Q)
    i = np.where(Q == q)[0][0] + 1  # +1 because Python uses 0-indexing
    v = 1 if floored_mod(lmin, lstep) < eps and lmin <= 0 and lmax >= 0 else 0
    return 1 - (i - 1) / (n - 1) - j + v


def simplicity_max(q, Q, j):
    """
    Calculate the maximum simplicity for a given q and j.

    Parameters
    ----------
    q : float
        The nice number being evaluated.
    Q : array-like
        The set of nice numbers for label steps.
    j : int
        The power of 10 scaling factor applied to the label step.

    Returns
    -------
    float
        The maximum simplicity score for the given q and j.
    """
    n = len(Q)
    i = np.where(Q == q)[0][0] + 1
    v = 1
    return 1 - (i - 1) / (n - 1) - j + v


def coverage(dmin, dmax, lmin, lmax):
    """
    Calculate the coverage score of the labeling scheme.

    Parameters
    ----------
    dmin : float
        The minimum data value on the axis.
    dmax : float
        The maximum data value on the axis.
    lmin : float
        The minimum label value in the labeling scheme.
    lmax : float
        The maximum label value in the labeling scheme.

    Returns
    -------
    float
        The coverage score for the labeling scheme.
    """
    range_ = dmax - dmin
    return 1 - 0.5 * ((dmax - lmax) ** 2 + (dmin - lmin) ** 2) / ((0.1 * range_) ** 2)


def coverage_max(dmin, dmax, span):
    """
    Calculate the maximum possible coverage for a given span.

    Parameters
    ----------
    dmin : float
        The minimum data value on the axis.
    dmax : float
        The maximum data value on the axis.
    span : float
        The total span of the labels.

    Returns
    -------
    float
        The maximum coverage score for the given span.
    """
    range_ = dmax - dmin
    if span > range_:
        half = (span - range_) / 2
        return 1 - 0.5 * (half**2 + half**2) / ((0.1 * range_) ** 2)
    else:
        return 1


def density(k, m, dmin, dmax, lmin, lmax):
    """
    Calculate the density score for a proposed set of labels.

    Parameters
    ----------
    k : int
        The number of labels.
    m : int
        The desired number of labels.
    dmin : float
        The minimum data value on the axis.
    dmax : float
        The maximum data value on the axis.
    lmin : float
        The minimum label value in the labeling scheme.
    lmax : float
        The maximum label value in the labeling scheme.

    Returns
    -------
    float
        The density score for the labeling scheme.
    """
    r = (k - 1) / (lmax - lmin)
    rt = (m - 1) / (max(lmax, dmax) - min(dmin, lmin))
    return 2 - max(r / rt, rt / r)


def density_max(k, m):
    """
    Calculate the maximum possible density for a given number of labels and desired labels.

    Parameters
    ----------
    k : int
        The number of labels.
    m : int
        The desired number of labels.

    Returns
    -------
    float
        The maximum density score for the given number of labels and desired labels.
    """
    if k >= m:
        return 2 - (k - 1) / (m - 1)
    else:
        return 1


def legibility(lmin, lmax, lstep):
    """
    Calculate a constant legibility score for label ranges.

    This function assumes legibility tests were done in a different programming environment (C#) and sets a constant value.

    Parameters
    ----------
    lmin : float
        The minimum value of the label range.
    lmax : float
        The maximum value of the label range.
    lstep : float
        The step value between labels in the range.

    Returns
    -------
    int
        The constant legibility score, which is set to 1 by default.
    """
    return 1


def extended(
    dmin,
    dmax,
    m,
    Q=np.array([1, 5, 2, 2.5, 4, 3]),
    only_loose=False,
    w=np.array([0.2, 0.25, 0.5, 0.05]),
):
    """
    Calculate an extended set of label ranges that aim to maximize a weighted score based on simplicity, coverage, and density.

    This function iteratively explores various combinations of label ranges and steps to find the one with the best score.

    Parameters
    ----------
    dmin : float
        The minimum value of the data range.
    dmax : float
        The maximum value of the data range.
    m : int
        The desired number of labels.
    Q : ndarray, optional
        The set of simplicity quotients to consider.
    only_loose : bool, optional
        A flag to indicate if only 'loose' label ranges should be considered. 'Loose' ranges cover beyond the data range.
    w : ndarray, optional
        The set of weights for the scoring components: simplicity, coverage, density, and legibility.

    Returns
    -------
    ndarray
        The array of labels that provides the best weighted score.
    """

    n = len(Q)
    # Initialize the best score as very low to ensure any score will be better
    best = {"score": -2}  

    j = 1
    while True:
        for q in Q:
            sm = simplicity_max(q, Q, j)

            if w[1] * sm + w[2] + w[3] + w[4] < best["score"]:
                return np.arange(
                    best["lmin"], best["lmax"] + best["lstep"], best["lstep"]
                )

            k = 2
            while True:
                dm = density_max(k, m)

                if w[1] * sm + w[2] + w[3] * dm + w[4] < best["score"]:
                    break

                delta = (dmax - dmin) / (k + 1) / j / q
                z = np.ceil(np.log10(delta))

                while True:
                    step = j * q * 10**z
                    cm = coverage_max(dmin, dmax, step * (k - 1))

                    if w[1] * sm + w[2] * cm + w[3] * dm + w[4] < best["score"]:
                        break

                    min_start = np.floor(dmax / step) * j - (k - 1) * j
                    max_start = np.ceil(dmin / step) * j

                    if min_start > max_start:
                        z += 1
                        continue

                    for start in range(int(min_start), int(max_start) + 1):
                        lmin = start * (step / j)
                        lmax = lmin + step * (k - 1)
                        lstep = step

                        c = coverage(dmin, dmax, lmin, lmax)
                        s = simplicity(q, Q, j, lmin, lmax, lstep)
                        g = density(k, m, dmin, dmax, lmin, lmax)
                        l = legibility(lmin, lmax, lstep)

                        score = w[1] * c + w[2] * s + w[3] * g + w[4] * l

                        if score > best["score"] and (
                            not only_loose or (lmin <= dmin and lmax >= dmax)
                        ):
                            best = {
                                "score": score,
                                "lmin": lmin,
                                "lmax": lmax,
                                "lstep": lstep,
                            }

                    z += 1
                k += 1
        j += 1