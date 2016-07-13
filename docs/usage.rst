Usage
=====

Woody has a command line interface::

  $ woody -h
    usage: woody [-h] [--debug] command ...

    positional arguments:
      command
        h2x       convert HTML to XHTML

    optional arguments:
      -h, --help  show this help message and exit
      --debug     enable debug messages

The :command:`h2x` command converts an HTML input to XHTML. It takes the file
name as input and prints the converted content to stdout. If the input file
name is given as ``-`` it will read the content from stdin and therefore it
can be used as part of a pipe::

  $ woody h2x foo.html
  ...
  $ cat foo.html | woody h2x -
  ...
