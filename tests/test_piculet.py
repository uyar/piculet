from pkg_resources import get_distribution

import piculet


def test_version():
    assert get_distribution("piculet").version == piculet.__version__
