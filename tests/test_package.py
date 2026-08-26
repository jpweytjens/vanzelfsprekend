from importlib.metadata import version

import vanzelfsprekend as vzs


def test_package_imports():
    assert vzs is not None


def test_version_matches_installed_metadata():
    assert vzs.__version__ == version("vanzelfsprekend")
