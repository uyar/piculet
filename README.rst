|pypi| |license| |azure| |codecov|

.. |pypi| image:: https://img.shields.io/pypi/v/piculet.svg?style=flat-square
    :target: https://pypi.org/project/piculet/
    :alt: PyPI version.

.. |license| image:: https://img.shields.io/pypi/l/piculet.svg?style=flat-square
    :target: https://pypi.org/project/piculet/
    :alt: Project license.

.. |azure| image:: https://dev.azure.com/tekir/piculet/_apis/build/status/uyar.piculet?branchName=master
    :target: https://dev.azure.com/tekir/piculet/_build
    :alt: Azure Pipelines build status.

.. |codecov| image:: https://codecov.io/gh/uyar/piculet/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/uyar/piculet

Piculet is a module for extracting data from XML or HTML documents
using XPath queries.
It consists of a `single source file`_ with no dependencies other than
the standard library, which makes it very easy to integrate into applications.
It also provides a command line interface.

Getting started
---------------

Piculet has been tested with Python 3.5+ and compatible versions of PyPy.
You can install the latest version using ``pip``::

    pip install piculet

.. _single source file: https://github.com/uyar/piculet/blob/master/piculet.py

Getting help
------------

The documentation is available on: https://piculet.tekir.org/

The source code can be obtained from: https://github.com/uyar/piculet

License
-------

Copyright (C) 2014-2019 H. Turgut Uyar <uyar@tekir.org>

Piculet is released under the LGPL license, version 3 or later.
Read the included `LICENSE.txt`_ file for details.

.. _LICENSE.txt: https://github.com/uyar/piculet/blob/master/LICENSE.txt
