Overview
========

The processing of a document consists of several stages:

#. Building a DOM tree out of the document.

#. (Optional) Preprocessing the tree.
   In some cases it might be helpful to modify the tree
   to simplify the extraction process.

#. Extracting data out of the tree.

#. (Optional) Postprocessing the collected data.

The operations are expressed in a scraping specification in JSON format.
