import logging
import os


def setup_logger(name, log_file='./logs/VectorVision.log', level=logging.DEBUG):
    """
    Set up a logger with a specific name, log file, and log level.
    """
    # Create a logger with the given name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create file handler if it doesn't exist
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(filename)s | %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Create stream handler if it doesn't exist
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(filename)s | %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger
