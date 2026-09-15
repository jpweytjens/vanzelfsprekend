"""The example datasets, shipped with the package.

Each is a CSV whose header comments name its source and licence;
`describe` returns them and `load` reads the table. The names:

- `anscombe`: Anscombe's quartet, four x,y sets with near-identical summary statistics.
- `co2_stations_monthly`: monthly mean CO2 at four stations.
- `grand_tour_speeds`: winners' average speed per grand tour edition, gaps as `nan`.
- `hadcrut5_annual`: annual global mean temperature anomaly, HadCRUT5.
- `mammals`: body and brain mass of land mammal species.
- `old_faithful`: Old Faithful eruption durations and the wait to the next.
- `planets`: semi-major axis and orbital period of the eight planets.
- `spm8_scenarios`: assessed warming per IPCC AR6 scenario, figure SPM.8.
"""

import io
from importlib.resources import files

import numpy as np

_FILES = files("vanzelfsprekend.datasets")

NAMES: tuple[str, ...] = tuple(
    sorted(
        path.name.removesuffix(".csv")
        for path in _FILES.iterdir()
        if path.name.endswith(".csv")
    )
)
"""The dataset names, one per shipped file."""


def _lines(name: str) -> list[str]:
    if name not in NAMES:
        raise ValueError(
            f"unknown dataset {name!r}; the datasets are {', '.join(NAMES)}"
        )
    return (_FILES / f"{name}.csv").read_text(encoding="utf-8").splitlines()


def load(name: str) -> np.ndarray:
    """Return dataset `name` as a structured array, one field per column.

    Parameters
    ----------
    name : str
        One of `NAMES`.

    Returns
    -------
    numpy.ndarray
        A structured array, so `load("old_faithful")["eruptions"]` is one
        column. Column types are inferred: integers, floats with `nan`
        for empty cells, text for text columns.

    Raises
    ------
    ValueError
        If `name` is not one of `NAMES`.
    """
    body = "\n".join(line for line in _lines(name) if not line.startswith("#"))
    return np.genfromtxt(
        io.StringIO(body), delimiter=",", names=True, dtype=None, encoding="utf-8"
    )


def describe(name: str) -> str:
    """Return dataset `name`'s source and licence, read from its file header.

    Parameters
    ----------
    name : str
        One of `NAMES`.

    Returns
    -------
    str
        The header comment lines, markers stripped, one per line.

    Raises
    ------
    ValueError
        If `name` is not one of `NAMES`.
    """
    return "\n".join(
        line.removeprefix("#").strip() for line in _lines(name) if line.startswith("#")
    )
