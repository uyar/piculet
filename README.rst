Piculet
=======

Piculet is a package for extracting data from XML documents using XPath
queries. It can also scrape web pages by first converting the HTML source
into XHTML. Piculet consists of a `single source file`_ with no dependencies
other than the standard library, which makes it very easy to integrate
into applications.

.. _single source file: https://bitbucket.org/uyar/piculet/src/tip/piculet.py

Piculet has been tested with Python 2.7, Python 3.4, and PyPy3 5.7.
You can install the latest version from PyPI::

   pip install piculet

.. note::

   If you want to try the development version, you can install it from
   the `Bitbucket repository`_::

      pip install hg+https://bitbucket.org/uyar/piculet

The Command-Line Interface
--------------------------

Installing Piculet creates a script named ``piculet`` which can be used
to invoke the command-line interface::

   $ piculet -h
   usage: piculet [-h] [--debug] command ...

The :command:`scrape` command downloads a document from a URL and
extracts data out of it as described by a specification file::

   $ piculet scrape -h
   usage: piculet scrape [-h] -s SPEC [--html] url

If the document is in HTML format, the ``--html`` option has to be used.
The specification file is in JSON format and contains the rules that define
how to extract the data [#rules]_. For example, to extract some data from
the Wikipedia page for `David Bowie`_, download the `wikipedia.json`_ file and
run the following command::

   piculet scrape -s wikipedia.json --html "https://en.wikipedia.org/wiki/David_Bowie"

This should give you the following output::

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

In the same command, change the name part of the URL to ``Muhammad_Ali`` and
you will get similar data for `Muhammad Ali`_. Note that since Wikipedia pages
are not well structured, the amount of data you get with this specification
file will vary.

Piculet can be used as an HTML to XHTML converter by invoking it with
the :command:`h2x` command. This command takes the file name as input
and prints the converted content, as in ``piculet h2x foo.html``. If the input
file name is given as ``-`` it will read the content from the standard input
and therefore can be used as part of a pipe:
``cat foo.html | piculet h2x -``

.. _Bitbucket repository: https://bitbucket.org/uyar/piculet
.. _wikipedia.json: https://bitbucket.org/uyar/piculet/src/tip/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie
.. _Muhammad Ali: https://en.wikipedia.org/wiki/Muhammad_Ali

.. [#rules]

   The rule grammar is explained in the :ref:`data_extraction` section.
