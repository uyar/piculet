Woody
=====

Woody is a package for extracting data from XML documents using XPath queries.
It can also scrape web pages by first converting the HTML source into XHTML.
Woody consists of a `single source file`_ with no dependencies other than
the standard library, which makes it very easy to integrate into applications.

.. _single source file: https://bitbucket.org/uyar/woody/src/tip/woody.py

You can install the latest version from PyPI::

   pip install woody

Or, if you like, you can install the development version from
the `Bitbucket repository <https://bitbucket.org/uyar/woody>`_::

   pip install hg+https://bitbucket.org/uyar/woody

To extract data from a document, you need to specify the rules for extraction.
This specification is in JSON format and you can find a few examples
in the `examples`_ folder.

.. _examples: https://bitbucket.org/uyar/woody/src/tip/examples

Although Woody is primarily aimed at developers, it also contains
a command-line interface where data extraction can be tested. To get an idea
about how Woody works, get the `wikipedia.json`_ specification example
and run the command given below to get some data out of the Wikipedia page
for `David Bowie`_::

   $ python woody.py scrape -s wikipedia.json -d person --param name=David_Bowie
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

Installing Woody through pip will create a script named ``woody`` which can
also be used to invoke the command-line interface::

   $ woody scrape -s wikipedia.json -d person --param name=John_Lennon

For a more complicated example, get the `imdb.json`_ specification and
run the following command to get details about the movie `The Shining`_::

   $ woody scrape -s imdb.json -d movie_combined --param imdb_id=81505

.. _wikipedia.json: https://bitbucket.org/uyar/woody/src/tip/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie

.. _imdb.json: https://bitbucket.org/uyar/woody/src/tip/examples/imdb.json
.. _The Shining: http://akas.imdb.com/title/tt0081505/combined