import logging


def getLogger(name, file_name, fmt="%(message)s", terminator="\n"):
    logger = logging.getLogger(name)
    # cHandle = logging.StreamHandler()
    cHandle = logging.FileHandler(filename=file_name)
    cHandle.terminator = terminator
    cHandle.setFormatter(logging.Formatter(fmt=fmt))
    logger.addHandler(cHandle)
    return logger
