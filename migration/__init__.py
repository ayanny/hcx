import logging
from rich.console import Console
from os.path import dirname, abspath

ROOT_DIR = dirname(abspath(__file__))

# initialize console
console = Console()

# create logger
logger = logging.getLogger(__name__)

# set log level
logger.setLevel(logging.DEBUG)

# define file handler and set formatter
file_handler = logging.FileHandler("log.txt")
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)
