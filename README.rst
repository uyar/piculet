Piculet
=======

Piculet is a package for extracting data from XML documents using XPath
queries. It can also scrape web pages by first converting the HTML source
into XHTML. Piculet consists of a `single source file`_ with no dependencies
other than the standard library, which makes it very easy to integrate
into applications.

.. _single source file: https://bitbucket.org/uyar/piculet/src/tip/piculet.py

Piculet requires Python 3.4 or later. You can install the latest version
from PyPI::

   pip install piculet

Or, if you like, you can install the development version from
the `Bitbucket repository <https://bitbucket.org/uyar/piculet>`_::

   pip install hg+https://bitbucket.org/uyar/piculet

To extract data from a document, you need to specify the rules for extraction.
This specification is in JSON format and you can find a few examples
in the `examples`_ folder.

.. _examples: https://bitbucket.org/uyar/piculet/src/tip/examples

Although Piculet is primarily aimed at developers, it also contains
a command-line interface where data extraction can be tested. To get an idea
about how Piculet works, get the `wikipedia.json`_ specification example
and run the command given below to get some data out of the Wikipedia page
for `David Bowie`_::

   $ python piculet.py scrape "https://en.wikipedia.org/wiki/David_Bowie" -s wikipedia.json -r person --html
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

Installing Piculet through pip will create a script named ``piculet`` which can
also be used to invoke the command-line interface::

   $ piculet scrape "https://en.wikipedia.org/wiki/John_Lennon" -s wikipedia.json -r person --html

For a more complicated example, get the `imdb.json`_ specification and
run the following command to get details about the movie `The Shining`_::

   $ piculet scrape "http://akas.imdb.com/title/tt0081505/combined" -s imdb.json -r movie_combined --html

.. _wikipedia.json: https://bitbucket.org/uyar/piculet/src/tip/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie

.. _imdb.json: https://bitbucket.org/uyar/piculet/src/tip/examples/imdb.json
.. _The Shining: http://akas.imdb.com/title/tt0081505/combined
