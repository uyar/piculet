Piculet is a package for extracting data from XML documents using XPath
queries. It can also scrape web pages by first converting the HTML source
into XHTML. Piculet consists of a `single source file`_ with no dependencies
other than the standard library, which makes it very easy to integrate
into applications.

.. _single source file: https://bitbucket.org/uyar/piculet/src/tip/piculet.py

:PyPI: https://pypi.python.org/pypi/piculet/
:Repository: https://bitbucket.org/uyar/piculet
:Documentation: https://piculet.readthedocs.io/

Piculet has been tested with Python 2.7, Python 3.4, and PyPy3 5.7.
You can install the latest version from PyPI::

   pip install piculet

.. note::

   If you want to use the development version, which could have more features
   but also be less stable, you can install it from the repository::

      pip install hg+https://bitbucket.org/uyar/piculet

The Command-Line Interface
--------------------------

Installing Piculet creates a script named ``piculet`` which can be used
to invoke the command-line interface::

   $ piculet -h
   usage: piculet [-h] [--debug] command ...

The ``scrape`` command downloads a document from a URL and extracts data
out of it as described by a specification file::

   $ piculet scrape -h
   usage: piculet scrape [-h] -s SPEC [--html] url

If the document is in HTML format, the ``--html`` option has to be used.
The specification file is in JSON format and contains the rules that define
how to extract the data. For example, to extract some data
from the Wikipedia page for `David Bowie`_, download the `wikipedia.json`_ file
and run the following command::

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
with this specification file will also vary.

Piculet can be used as an HTML to XHTML convertor by invoking it with
the ``h2x`` command. This command takes the file name as input and prints
the converted content, as in ``piculet h2x foo.html``. If the input file name
is given as ``-`` it will read the content from the standard input
and therefore can be used as part of a pipe:
``cat foo.html | piculet h2x -``

.. _Bitbucket repository: https://bitbucket.org/uyar/piculet
.. _wikipedia.json: https://bitbucket.org/uyar/piculet/src/tip/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie
.. _Merlene Ottey: https://en.wikipedia.org/wiki/Merlene_Ottey
