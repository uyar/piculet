from importlib import metadata

import piculet


def test_installed_version_should_match_tested_version():
    assert metadata.version("piculet") == piculet.__version__
