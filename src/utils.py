import logging
import numpy as np
from datetime import datetime


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def get_logger():
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    return logger


def datetime_string_to_timestamp_ms(
    date_str: str, date_format: str = "%Y-%m-%d %H:%M:%S"
):
    """
    Convert a datetime string to a timestamp in milliseconds.

    Parameters:
    - date_str: the datetime string to be converted.
    - date_format: the format of the datetime string. Default is '%Y-%m-%d %H:%M:%S'.

    Returns:
    - Timestamp in milliseconds.
    """
    dt_object = datetime.strptime(date_str, date_format)
    timestamp_ms = int(dt_object.timestamp() * 1000)
    return timestamp_ms
