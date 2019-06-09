History
=======

2.0.0 (unreleased)
------------------

- Drop support for Python 2 and 3.4.
- Cache compiled XPath expressions.
- Remove HTML charset detection.

1.0.1 (2019-02-07)
------------------

- Accept both .yaml and .yml as valid YAML file extensions.
- Documentation fixes.

1.0 (2018-05-25)
----------------

- Bumped version to 1.0.

1.0b7 (2018-03-21)
------------------

- Dropped support for Python 3.3.
- Fixes for handling Unicode data in HTML for Python 2.
- Added registry for preprocessors.

1.0b6 (2018-01-17)
------------------

- Support for writing specifications in YAML.

1.0b5 (2018-01-16)
------------------

- Added a class-based API for writing specifications.
- Added predefined transformation functions.
- Removed callables from specification maps. Use the new API instead.
- Added support for registering new reducers and transformers.
- Added support for defining sections in document.
- Refactored XPath evaluation method in order to parse path expressions once.
- Preprocessing will be done only once when the tree is built.
- Concatenation is now the default reducing operation.

1.0b4 (2018-01-02)
------------------

- Added "--version" option to command line arguments.
- Added option to force the use of lxml's HTML builder.
- Fixed the error where non-truthy values would be excluded from the result.
- Added support for transforming node text during preprocess.
- Added separate preprocessing function to API.
- Renamed the "join" reducer as "concat".
- Renamed the "foreach" keyword for keys as "section".
- Removed some low level debug messages to substantially increase speed.

1.0b3 (2017-07-25)
------------------

- Removed the caching feature.

1.0b2 (2017-06-16)
------------------

- Added helper function for getting cache hash keys of URLs.

1.0b1 (2017-04-26)
------------------

- Added optional value transformations.
- Added support for custom reducer callables.
- Added command-line option for scraping documents from local files.

1.0a2 (2017-04-04)
------------------

- Added support for Python 2.7.
- Fixed lxml support.

1.0a1 (2016-08-24)
------------------

- First release on PyPI.
