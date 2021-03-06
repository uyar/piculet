Piculet is a module for extracting data from XML or HTML documents
using XPath queries.
It consists of a `single source file`_ with no dependencies other than
the standard library,
which makes it very easy to integrate into applications.
It also provides a command line interface.

.. _single source file: https://github.com/uyar/piculet/blob/master/piculet.py

Piculet is used for the parsers
of the `IMDbPY <https://github.com/alberanid/imdbpy>`_ project.

Getting started
---------------

Piculet works with Python 3.6 and later versions.
You can install it using ``pip``::

    pip install piculet

Installing Piculet creates a script named ``piculet`` which can be used
to invoke the command line interface::

   $ piculet -h
   usage: piculet [-h] [--version] [--html] (-s SPEC | --h2x)

For example, say you want to extract some data from the file `shining.html`_.
An example specification is given in `movie.json`_.
Download both of these files and run the command::

   $ cat shining.html | piculet -s movie.json

.. _shining.html: https://github.com/uyar/piculet/blob/master/examples/shining.html
.. _movie.json: https://github.com/uyar/piculet/blob/master/examples/movie.json

Getting help
------------

The documentation is available on: https://piculet.readthedocs.io/

The source code can be obtained from: https://github.com/uyar/piculet

License
-------

Copyright (C) 2014-2021 H. Turgut Uyar <uyar@tekir.org>

Piculet is released under the LGPL license, version 3 or later.
Read the included `LICENSE.txt`_ file for details.

.. _LICENSE.txt: https://github.com/uyar/piculet/blob/master/LICENSE.txt
