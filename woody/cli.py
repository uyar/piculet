# Copyright (C) 2016 H. Turgut Uyar <uyar@tekir.org>
#
# This file is part of Woody.
#
# Woody is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Woody is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Woody.  If not, see <http://www.gnu.org/licenses/>.

"""
This is the module that cantains the console utility.
"""

import logging
import os
import sys

from argparse import ArgumentParser

from .web import html_to_xhtml


_logger = logging.getLogger(__name__)


def _get_parser():
    """Get a parser for command line arguments."""

    def h2x(arguments):
        _logger.debug('converting HTML to XHTML')
        if arguments.file == '-':
            _logger.debug('reading from stdin')
            content = sys.stdin.read()
        else:
            filename = os.path.abspath(arguments.file)
            _logger.debug('reading from file: %s', filename)
            with open(filename) as f:
                content = f.read()
        print(html_to_xhtml(content), end='')

    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='enable debug messages')

    commands = parser.add_subparsers(metavar='command', dest='command')

    subparser = commands.add_parser('h2x', help='convert HTML to XHTML')
    subparser.set_defaults(func=h2x)
    subparser.add_argument('file', help='file to convert')

    return parser


def main():
    """Entry point of the command line utility."""
    parser = _get_parser()
    arguments = parser.parse_args()

    # set debug mode
    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
        _logger.debug('running in debug mode')

    # run the handler for the selected command
    try:
        arguments.func(arguments)
    except AttributeError:
        parser.print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
