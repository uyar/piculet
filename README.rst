Copyright (C) 2014-2018 H. Turgut Uyar <uyar@tekir.org>

Piculet is a utility for extracting data from XML or HTML documents
using XPath queries. It consists of a `single source file`_
with no dependencies other than the standard library, which makes it very easy
to integrate into applications.

.. _single source file: https://bitbucket.org/uyar/piculet/src/tip/piculet.py

:PyPI: https://pypi.python.org/pypi/piculet/
:Repository: https://bitbucket.org/uyar/piculet
:Documentation: https://piculet.readthedocs.io/

Piculet has been tested with Python 2.7, Python 3.3+, PyPy2 5.7+,
and PyPy3 5.7+. You can install the latest version from PyPI::

   pip install piculet

Overview
--------

Scraping a document consists of three stages:

#. Building a DOM tree out of the document. This is a straightforward
   operation for an XML document. For an HTML document, Piculet will first
   try to convert it into XHTML and then build the tree from that.

#. Preprocessing the tree. This is an optional stage. In some cases
   it might be helpful to do some changes on the tree to simplify
   the extraction process.

#. Extracting data out of the tree.

The preprocessing and extraction stages are expressed as part of a scraping
specification. The specification is a mapping which can be stored
in a file format that can represent a mapping, such as JSON or YAML.
Details about the specification are given in later chapters.

Command Line Interface
----------------------

Installing Piculet creates a script named ``piculet`` which can be used
to invoke the command line interface::

   $ piculet -h
   usage: piculet [-h] [--debug] command ...

The ``scrape`` command extracts data out of a document as described by
a specification file::

   $ piculet scrape -h
   usage: piculet scrape [-h] -s SPEC [--html] document

The location of the document can be given as a file path or a URL.
For example, say you want to extract some data from the file `shining.html`_.
An example specification is given in `movie.json`_ [#yaml]_.
Download both these files and run the command::

   $ piculet scrape -s movie.json shining.html

This should print the following output::

   {
     "cast": [
       {
         "character": "Jack Torrance",
         "link": "/people/2",
         "name": "Jack Nicholson"
       },
       {
         "character": "Wendy Torrance",
         "link": "/people/3",
         "name": "Shelley Duvall"
       }
     ],
     "director": {
       "link": "/people/1",
       "name": "Stanley Kubrick"
     },
     "genres": [
       "Horror",
       "Drama"
     ],
     "language": "English",
     "review": "Fantastic movie. Definitely recommended.",
     "runtime": "144 minutes",
     "title": "The Shining",
     "year": 1980
   }

For HTML documents, the ``--html`` option has to be used. If the document
address starts with ``http://`` or ``https://``, the content will be taken
from the given URL. For example, to extract some data from the Wikipedia page
for `David Bowie`_, download the `wikipedia.json`_ file and run the command::

   piculet scrape -s wikipedia.json --html "https://en.wikipedia.org/wiki/David_Bowie"

This should print the following output::

   {
     "birthplace": "Brixton, London, England",
     "born": "1947-01-08",
     "died": "2016-01-10",
     "name": "David Bowie",
     "occupation": [
       "Singer",
       "songwriter",
       "actor"
     ]
   }

In the same command, change the name part of the URL to ``Merlene_Ottey`` and
you will get similar data for `Merlene Ottey`_. Note that since the markup
used in Wikipedia pages for persons varies, the kinds of data you get
with this specification will also vary.

Piculet can be used as an HTML to XHTML convertor by invoking it with
the ``h2x`` command. This command takes the file name as input and prints
the converted content, as in ``piculet h2x foo.html``. If the input file name
is given as ``-`` it will read the content from the standard input
and therefore can be used as part of a pipe:
``cat foo.html | piculet h2x -``

Using in programs
-----------------

The scraping operation can also be invoked programmatically using
the :func:`scrape_document <piculet.scrape_document>` function:

.. code-block:: python

   from piculet import scrape_document

   url = 'https://en.wikipedia.org/wiki/David_Bowie'
   spec = 'wikipedia.json'
   data = scrape_document(url, spec, content_format='html')

.. [#yaml]

   A YAML configuration example can be found in `movie.yaml`_.
   For YAML support, install Piculet using the command
   ``pip install piculet[yaml]``. Note that this creates an
   external dependency.

.. _shining.html: https://bitbucket.org/uyar/piculet/src/tip/examples/shining.html
.. _movie.json: https://bitbucket.org/uyar/piculet/src/tip/examples/movie.json
.. _movie.yaml: https://bitbucket.org/uyar/piculet/src/tip/examples/movie.yaml
.. _wikipedia.json: https://bitbucket.org/uyar/piculet/src/tip/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie
.. _Merlene Ottey: https://en.wikipedia.org/wiki/Merlene_Ottey
