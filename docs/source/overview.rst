Overview
========

Scraping a document consists of three stages:

#. Building a DOM tree out of the document.
   This is a straightforward operation for an XML document.
   For an HTML document, Piculet will first try to convert it into XHTML,
   and then build the tree from that.

#. Preprocessing the tree.
   This is an optional stage.
   In some cases it might be helpful to do some changes on the tree
   to simplify the extraction process.

#. Extracting data out of the tree.

The preprocessing and extraction stages are expressed
as part of a scraping specification.
The specification is a mapping which can be stored in a file format
that can represent a mapping, such as JSON.
Details about the specification are given in later chapters.

Command-line interface
----------------------

The command-line interface reads the document from the standard input.
After downloading the example files `shining.html`_ and `movie.json`_,
run the command::

   $ cat shining.html | piculet -s movie.json

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

For HTML documents, the ``--html`` option has to be used.
For example, to extract some data from the Wikipedia page for `David Bowie`_,
download the `wikipedia.json`_ file and run the command::

   $ curl -s "https://en.wikipedia.org/wiki/David_Bowie" | piculet -s wikipedia.json --html

This should print the following output::

   {
     "birthplace": "Brixton, London, England",
     "born": "1947-01-08",
     "name": "David Bowie",
     "occupation": [
       "Singer",
       "songwriter",
       "actor"
     ]
   }

In the same command, change the name part of the URL to ``Merlene_Ottey``
and you will get similar data for `Merlene Ottey`_.
Note that since the markup used in Wikipedia pages for persons varies,
the kinds of data you get with this specification will also vary.

Piculet can also be used as a simplistic HTML to XHTML converter
by invoking it with the ``--h2x`` option::

  $ cat foo.html | piculet --h2x

.. _shining.html: https://github.com/uyar/piculet/blob/master/examples/shining.html
.. _movie.json: https://github.com/uyar/piculet/blob/master/examples/movie.json
.. _wikipedia.json: https://github.com/uyar/piculet/blob/master/examples/wikipedia.json
.. _David Bowie: https://en.wikipedia.org/wiki/David_Bowie
.. _Merlene Ottey: https://en.wikipedia.org/wiki/Merlene_Ottey
