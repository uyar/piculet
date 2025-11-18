Overview
========

The processing of a document consists of several stages:

#. Building a tree out of the document.
#. (Optional) Preprocessing the tree.
#. Extracting data out of the tree.
#. (Optional) Postprocessing the collected data.

The extraction process generates a dictionary according to a specification
that describes what the names of the keys will be
and how their values will be extracted.
The specification is itself a dictionary with the following keys:

*doctype* (required)
    A string indicating the type of the document.
    Possible values are ``html``, ``xml`` and ``json``.

*pre*
    The list of names of preprocessors to apply to the document tree
    before extraction.

*rules* (required)
    The list of rules to apply to the document tree to extract the data.

*post*
    The list of names of postprocessors to apply to the obtained data
    after extraction.
