import logging
import os


logging.raiseExceptions = False

os.environ['PICULET_WEB_CACHE'] = os.path.join(os.path.dirname(__file__), '.cache')
