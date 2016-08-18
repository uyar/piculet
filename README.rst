Woody
=====

Woody is a library for extracting data from XML documents using XPath queries.
It also contains an HTML cleaner which can be used to convert HTML into XHTML
so that web pages can also be scraped.

Woody consists of a single source file with no dependencies other than
the standard library. Therefore it is very easy to bundle within applications.

To extract the data, you need to supply a specification that describes
how to extract the data from the document. The specification is in JSON format
and a few examples are provided in the :file:`examples` folder.
