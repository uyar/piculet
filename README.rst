Woody
=====

Woody is a package for extracting data from XML documents using XPath queries.
It can also scrape web pages by first converting the HTML source into XHTML.
Woody consists of a single source file with no dependencies other than
the standard library, which makes it very easy to integrate into applications.

You can install the latest version from PyPI using the command::

   pip install woody

Or, if you like, you can install the development version using the command::

   pip install hg+https://bitbucket.org/uyar/woody

To extract data from a document, you need to specify the rules for extraction.
This specification is in JSON format and you can find a few examples in the
:file:`examples` folder.

Although Woody is primarily aimed at developers, it also contains a
command-line interface where data extraction can be tested. To get an idea
about how Woody works, get the :file:`wikipedia.json` specification example
and run the command::

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

.. note::

   Installing Woody through pip will create a script named ``woody`` which can
   also be used to invoke the command-line interface::

      $ woody scrape -s wikipedia.json -d person --param name=John_Lennon

For a more complicated example, try::

   $ python woody.py scrape -s imdb.json -d movie_combined --param imdb_id=133093