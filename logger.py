import json
import logging.config
from logging import getLogger, basicConfig, DEBUG, FileHandler, ERROR, StreamHandler
from config.settings import BASE_DIR
from os.path import sep

with open(f'{BASE_DIR}{sep}logging.conf') as file:
    config = json.load(file)

logging.config.dictConfig(config)

log = getLogger()
# FORMAT = '%(asctime)s : %(name)s : %(levelname)s : %(message)s'
#
# path = f"{BASE_DIR}{sep}logs{sep}errors.log"
#
# file_handler = FileHandler(path)
# file_handler.setLevel(ERROR)
#
# console = StreamHandler()
# console.setLevel(DEBUG)
#
# basicConfig(level=DEBUG, format=FORMAT, handlers=(file_handler, console))

if __name__ == '__main__':
    log.error('test')
