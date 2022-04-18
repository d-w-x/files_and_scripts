import logging
from io import StringIO

LOG_STR = StringIO()

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
log = logging.getLogger()
fh = logging.StreamHandler(stream=LOG_STR)
log.addHandler(fh)
