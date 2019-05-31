|pypi| |support| |license| |pipelines| |black|

.. |pypi| image:: https://img.shields.io/pypi/v/piculet.svg?style=flat-square
    :target: https://pypi.org/project/piculet/
    :alt: PyPI version.

.. |support| image:: https://img.shields.io/pypi/pyversions/piculet.svg?style=flat-square
    :target: https://pypi.org/project/piculet/
    :alt: Supported Python versions.

.. |license| image:: https://img.shields.io/pypi/l/piculet.svg?style=flat-square
    :target: https://pypi.org/project/piculet/
    :alt: Project license.

.. |pipelines| image:: https://dev.azure.com/tekir/piculet/_apis/build/status/uyar.piculet?branchName=master
    :target: https://dev.azure.com/tekir/piculet/_build
    :alt: Azure Pipelines build status.

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square
    :target: https://github.com/python/black
    :alt: Code formatted by Black.

Piculet is a module for extracting data from XML or HTML documents
using XPath queries. It consists of a `single source file`_
with no dependencies other than the standard library, which makes it very easy
to integrate into applications. It also provides a command line interface.

Getting started
---------------

Piculet has been tested with Python 2.7, Python 3.4+, and compatible
versions of PyPy. You can install the latest version using ``pip``::

    pip install piculet

.. _single source file: https://github.com/uyar/piculet/blob/master/piculet.py

Getting help
------------

The documentation is available on: https://piculet.tekir.org/

The source code can be obtained from: https://github.com/uyar/piculet

License
-------

Copyright (C) 2014-2019 H. Turgut Uyar <uyar@tekir.org>

Piculet is released under the LGPL license, version 3 or later. Read
the included ``LICENSE.txt`` for details.
