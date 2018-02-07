import sys
import logging
from logging.handlers import RotatingFileHandler

# Setup the log handlers to stdout and file.
log = logging.getLogger('imap_monitor')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
handler_stdout = logging.StreamHandler(sys.stdout)
handler_stdout.setLevel(logging.DEBUG)
handler_stdout.setFormatter(formatter)
log.addHandler(handler_stdout)
handler_file = RotatingFileHandler(
	'imap_monitor.log',
	mode='a',
	maxBytes=1048576,
	backupCount=9,
	encoding='UTF-8',
	delay=True
	)
handler_file.setLevel(logging.DEBUG)
handler_file.setFormatter(formatter)
log.addHandler(handler_file)

def writeLog(type, content, USERNAME=""):
    if type == "info":
        log.info("%s ; %s" % (content, USERNAME))

    else:
        log.critical("%s ; %s" % (content, USERNAME))