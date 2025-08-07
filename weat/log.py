import logging

weatLog = None


def getLog():
    """Get the logger for the webeater module."""
    global weatLog
    if weatLog is None:
        logging.basicConfig(level=logging.INFO)
        weatLog = logging.getLogger("webeater")
        weatLog.setLevel(logging.INFO)
    return weatLog
