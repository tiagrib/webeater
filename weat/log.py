import logging
import coloredlogs

weatLog = None

__loggers = {}

LOG_FORMAT = "%(asctime)s.%(msecs)03d %(name)s:%(levelname)s:\t%(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVEL_STYLES = dict(coloredlogs.DEFAULT_LEVEL_STYLES)

# E.g. modify color styles
# LOG_LEVEL_STYLES["debug"]["color"] = "cyan"


def getLog(name=None):
    """Get the logger for the webeater module."""

    if name is None:
        name = "webeater"

    if name not in __loggers:
        ret_log = logging.getLogger(name)
        ret_log.setLevel(logging.INFO)

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
