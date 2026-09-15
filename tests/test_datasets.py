import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend import datasets


def test_names_are_the_eight_shipped_files():
    assert datasets.NAMES == (
        "anscombe",
        "co2_stations_monthly",
        "grand_tour_speeds",
        "hadcrut5_annual",
        "mammals",
        "old_faithful",
        "planets",
        "spm8_scenarios",
    )


@pytest.mark.parametrize("name", datasets.NAMES)
def test_every_dataset_loads_with_named_fields(name):
    table = datasets.load(name)
    assert table.dtype.names
    assert table.shape[0] > 0


def test_text_column_reads_as_text():
    planets = datasets.load("planets")
    assert (planets["name"] == "Earth").sum() == 1


def test_gaps_read_as_nan():
    speeds = datasets.load("grand_tour_speeds")
    assert np.isnan(speeds["vuelta"]).any()
    assert np.isfinite(speeds["tour"]).any()


def test_describe_returns_the_header_without_markers():
    text = datasets.describe("old_faithful")
    assert "Azzalini" in text
    assert not text.startswith("#")
    assert "\n#" not in text


def test_unknown_name_lists_the_names():
    with pytest.raises(ValueError, match="old_faithful"):
        datasets.load("nope")
    with pytest.raises(ValueError, match="old_faithful"):
        datasets.describe("nope")


def test_module_docstring_names_every_dataset():
    doc = datasets.__doc__ or ""
    documented = {
        line.split("`")[1]
        for line in doc.splitlines()
        if line.strip().startswith("- `")
    }
    assert documented == set(datasets.NAMES)


def test_datasets_is_public():
    assert "datasets" in vzs.__all__
    assert vzs.datasets is datasets
