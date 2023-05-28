Lower-level functions
=====================

Piculet also provides a lower-level API where you can run the stages
separately.
For example, if the same document will be scraped multiple times
with different rules, calling the ``scrape`` function repeatedly will cause
the document to be parsed into a DOM tree repeatedly.
Instead, you can create the DOM tree once,
and run extraction rules against this tree multiple times.

Also, this API uses code to express the specification (instead of strings)
and therefore development tools can help better in writing the rules
by showing error indicators and suggesting autocompletions.

Building the tree
-----------------

The DOM tree can be created from the document using
the :func:`build_tree <piculet.build_tree>` function:

.. code-block:: python

   >>> from piculet import build_tree
   >>> root = build_tree(document)

If the document needs to be converted from HTML to XML, you can use
the :func:`html_to_xml <piculet.html_to_xml>` function:

.. code-block:: python

   >>> from piculet import html_to_xml
   >>> converted = html_to_xml(document)
   >>> root = build_tree(converted)

If lxml is available, you can use the ``html`` parameter for building
the tree without converting the HTML document into XML:

.. code-block:: python

   >>> root = build_tree(document, html=True)

.. note::

   Note that if you use the lxml.html builder, there might be differences
   about how the tree is built compared to the piculet conversion method,
   and the path queries for preprocessing and extraction might need changes.

Preprocessing
-------------

Preprocessors are functions that take an element in the DOM tree as parameter
and modify the tree.
The :attr:`preprocessors <piculet.preprocessors>` registry contains
preprocessor generators which take the parameters other than the element
to apply the operation to, and return a function that expects the element:

.. code-block:: python

   >>> from piculet import preprocessors
   >>> remove_ads = preprocessors.remove(path='//div[@class="ad"]')
   >>> remove_ads(root)

.. warning::

   The preprocessing functions assume that the root of the tree
   doesn't change.

Data extraction
---------------

The API for data extraction has a one-to-one correspondance
with the specification mapping.

:class:`Path <piculet.Path>` extractors are applied to elements
to extract the value for a single data item.

.. code-block:: python

   >>> from piculet import Path
   >>> path = Path('//span[@class="year"]/text()', transform=int)
   >>> path.extract(root)
   1980

The ``sep`` parameter can be used concatenate using a separator string:

.. code-block:: python

   >>> path = Path('//table[@class="cast"]/tr/td[1]/a/text()', sep=", ")
   >>> path.extract(root)
   'Jack Nicholson, Shelley Duvall'

Every item in the result mapping is generated
by a :class:`Rule <piculet.Rule>` in the API.
Rules are applied to elements to extract data items in the result mapping,
so their basic function is to associate the keys with the values.

.. code-block:: python

   >>> from piculet import Rule
   >>> rule = Rule(
   ...     key="year",
   ...     value=Path('//span[@class="year"]/text()', transform=int),
   ... )
   >>> rule.extract(root)
   {'year': 1980}

:class:`Piculet <piculet.Piculet>` extractors are applied to elements
to extract subitems for a data item.
Basically, they are rule collections.

.. code-block:: python

   >>> from piculet import Piculet
   >>> rules = [
   ...     Rule("title", Path('//title/text()')),
   ...     Rule("year", Path('//span[@class="year"]/text()', transform=int)),
   ... ]
   >>> items = Piculet(rules)
   >>> items.extract(root)
   {'title': 'The Shining', 'year': 1980}

Piculet extractors act both
as the top level extractor that gets applied to the root of the tree,
and also as an extractor for any rule with subitems.

An extractor can have a ``foreach`` parameter if it will be multi-valued:

.. code-block:: python

   >>> rules = [
   ...     Rule(
   ...         "genres",
   ...         Path(
   ...             foreach='//ul[@class="genres"]/li',
   ...             path="./text()",
   ...             transform=str.lower,
   ...         ),
   ...     ),
   ... ]
   >>> items = Piculet(rules)
   >>> items.extract(root)
   {'genres': ['horror', 'drama']}

The ``key`` parameter of a rule can be an extractor
in which case it can be used to extract the key value from content.
A rule can also have a ``foreach`` parameter
for generating multiple items in one rule.
These features will work as they are described in the data extraction section.

A more complete example with transformations is given below.
Again note that the specification is exactly the same as given
in the corresponding mapping example in the data extraction chapter.

.. code-block:: python

   >>> rules = [
   ...     Rule(
   ...         "cast",
   ...         Piculet(
   ...             foreach='//table[@class="cast"]/tr',
   ...             rules=[
   ...                 Rule("name", Path("./td[1]/a/text()")),
   ...                 Rule("character", Path("./td[2]/text()")),
   ...              ],
   ...              transform=lambda x: "%(name)s as %(character)s" % x
   ...         ),
   ...     ),
   ... ]
   >>> Piculet(rules).extract(root)
   {'cast': ['Jack Nicholson as Jack Torrance',
     'Shelley Duvall as Wendy Torrance']}

A rule can have a ``section`` parameter as described in the data extraction
chapter:

.. code-block:: python

   >>> rules = [
   ...     Rule(
   ...         "director",
   ...         Piculet(
   ...             section='//div[@class="director"]//a',
   ...             rules=[
   ...                 Rule("name", Path("./text()")),
   ...                 Rule("link", Path("./@href")),
   ...             ],
   ...         ),
   ...     ),
   ... ]
   >>> Piculet(rules).extract(root)
   {'director': {'name': 'Stanley Kubrick', 'link': '/people/1'}}
