Command-Line Interface
======================

The command line interface provides usage help::

   $ woody -h
   usage: woody [-h] [--debug] command ...

   positional arguments:
     command
       h2x       convert HTML to XHTML
       scrape    scrape a document

   optional arguments:
     -h, --help  show this help message and exit
     --debug     enable debug messages

The :command:`scrape` command scrapes a URL based on a specification and prints
the result::

   $ woody scrape -h
   usage: woody scrape [-h] -s SPEC -r RULES [--html] url

   positional arguments:
     url         URL to scrape

   optional arguments:
     -h, --help  show this help message and exit
     -s SPEC     spec file
     -r RULES    selected rule set in spec
     --html      document content is html

The :command:`h2x` command converts an HTML input to XHTML. It takes the file
name as input and prints the converted content to stdout. If the input file
name is given as ``-`` it will read the content from stdin and therefore it
can be used as part of a pipe::

   $ woody h2x foo.html
   ...
   $ cat foo.html | woody h2x -
   ...
