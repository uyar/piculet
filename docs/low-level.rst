
Lower-level functions
=====================

Piculet also provides a lower-level API where you can run the stages
separately. For example, if the same document will be scraped multiple times
with different rules, calling the ``scrape`` function repeatedly will cause
the document to be parsed into a DOM tree repeatedly. Instead, you can
create the DOM tree once and run extraction rules against this tree
multiple times.

Also, this API uses classes to express the specification and therefore
development tools can help better in writing the rules by showing error
indicators and suggesting autocompletions.

Building the tree
-----------------

The DOM tree can be created from the document using
the :func:`build_tree <piculet.build_tree>` function:

.. code-block:: python

   >>> from piculet import build_tree
   >>> root = build_tree(document)

If the document needs to be converted from HTML to XML, you can use
the :func:`html_to_xhtml <piculet.html_to_xhtml>` function:

.. code-block:: python

   >>> from piculet import html_to_xhtml
   >>> converted = html_to_xhtml(document)
   >>> root = build_tree(converted)

Preprocessing
-------------

The tree can be modified using the :func:`preprocess <piculet.preprocess>`
function:

.. code-block:: python

   >>> from piculet import preprocess
   >>> ops = [{'op': 'remove', 'path': '//div'}]
   >>> preprocess(root, ops)

Data extraction
---------------

The class-based API to data extraction has a one-to-one correspondance
with the specification mapping. A :class:`Rule <piculet.Rule>` object
corresponds to a key-value pair in the items list. Its value is produced
by an ``extractor``. In the simple case, an extractor is
a :class:`Path <piculet.Path>` object which is a combination of a path,
a reducer, and a transformer.

.. code-block:: python

   >>> from piculet import Path, Rule
   >>> extractor = Path('//span[@class="year"]/text()',
   ...                  reduce=reducers.first, transform=int)
   >>> rule = Rule(key='year', extractor=extractor)
   >>> rule.extract(root)
   {'year': 1980}

An extractor can have a ``foreach`` attribute if it will be multi-valued:

.. code-block:: python

   >>> extractor = Path(foreach='//ul[@class="genres"]/li',
   ...                  path='./text()', reduce=reducers.first,
   ...                  transform=str.lower)
   >>> rule = Rule(key='genres', extractor=extractor)
   >>> rule.extract(root)
   {'genres': ['horror', 'drama']}

The ``key`` attribute of a rule can be an extractor in which case it can be
used to extract the key value from content. A rule can also have a ``foreach``
attribute for generating multiple items in one rule. These features will work
as they are described in the data extraction section.

A :class:`Rules <piculet.Rules>` object contains a collection of rule objects
and it corresponds to the "items" part in the specification mapping. It acts
both as the top level extractor that gets applied to the root of the tree,
and also as an extractor for any rule with subrules.

.. code-block:: python

   >>> from piculet import Rules
   >>> rules = [Rule(key='title',
   ...               extractor=Path('//title/text()')),
   ...          Rule('year',
   ...               extractor=Path('//span[@class="year"]/text()', transform=int))]
   >>> Rules(rules).extract(root)
   {'title': 'The Shining', 'year': 1980}

A more complete example with transformations is below. Again note that,
the specification is exactly the same as given in the corresponding
mapping example in the data extraction chapter.

.. code-block:: python

   >>> rules = [
   ...     Rule(key='cast',
   ...          extractor=Rules(
   ...              foreach='//table[@class="cast"]/tr',
   ...              rules=[
   ...                  Rule(key='name',
   ...                       extractor=Path('./td[1]/a/text()')),
   ...                  Rule(key='character',
   ...                       extractor=Path('./td[2]/text()'))
   ...              ],
   ...              transform=lambda x: '%(name)s as %(character)s' % x
   ...          ))
   ... ]
   >>> Rules(rules).extract(root)
   {'cast': ['Jack Nicholson as Jack Torrance',
     'Shelley Duvall as Wendy Torrance']}

A rules object can have a ``section`` attribute as described in the data
extraction chapter:

.. code-block:: python

   >>> rules = [
   ...     Rule(key='director',
   ...          extractor=Rules(
   ...              section='//div[@class="director"]//a',
   ...              rules=[
   ...                  Rule(key='name',
   ...                       extractor=Path('./text()')),
   ...                  Rule(key='link',
   ...                       extractor=Path('./@href'))
   ...              ]))
   ... ]
   >>> Rules(rules).extract(root)
   {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}
