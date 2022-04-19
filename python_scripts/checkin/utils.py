import logging
from io import StringIO

LOG_STR = StringIO()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
)
log = logging.getLogger()
fh = logging.StreamHandler(stream=LOG_STR)
fh.setLevel(level=logging.INFO)
fh.setFormatter(logging.Formatter('%(asctime)s[%(levelname)-8s] - %(message)s',
                                  datefmt='%m-%d %H:%M:%S'))
log.addHandler(fh)
