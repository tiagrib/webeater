import logging
import coloredlogs

weatLog = None

__loggers = {}

LOG_FORMAT = "%(asctime)s.%(msecs)03d %(name)s:%(levelname)s:\t%(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVEL_STYLES = dict(coloredlogs.DEFAULT_LEVEL_STYLES)

# E.g. modify color styles
# LOG_LEVEL_STYLES["debug"]["color"] = "cyan"

global log_debug
log_debug = False

global log_silent
log_silent = False


def setLogDebug(debug: bool):
    """Set the global debug flag for logging."""
    global log_debug
    log_debug = debug


def setLogSilent(silent: bool):
    """Set the global silent flag for logging."""
    global log_silent
    log_silent = silent


def getLog(name=None):
    """Get the logger for the webeater module."""

    if name is None:
        name = "webeater"

    if name not in __loggers:
        ret_log = logging.getLogger(name)
        global log_debug, log_silent

        # Set log level based on silent and debug flags
        if log_silent:
            ret_log.setLevel(logging.ERROR)  # Only show errors in silent mode
        else:
            ret_log.setLevel(logging.DEBUG if log_debug else logging.INFO)

        coloredlogs.install(
            level=ret_log.level,
            logger=ret_log,
            fmt=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
            reconfigure=True,
        )

        __loggers[name] = ret_log
    else:
        ret_log = __loggers[name]

    return ret_log
