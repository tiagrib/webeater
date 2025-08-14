import logging

weatLog = None


def getLog(name=None):
    """Get the logger for the webeater module."""
    if name is None:
        global weatLog
        if weatLog is None:
            weatLog = logging.getLogger("webeater")
            logging.basicConfig(level=logging.INFO)
        ret_log = weatLog

    else:
        ret_log = logging.getLogger(name)

    ret_log.setLevel(logging.INFO)
    return ret_log
