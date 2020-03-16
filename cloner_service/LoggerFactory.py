from logging import getLogger, Formatter, StreamHandler, DEBUG
from logging.config import fileConfig


class LoggerFactory:
    def __init__(self):
        pass

    @staticmethod
    def create_console_logger(name, level=DEBUG):
        # create logger
        logger = getLogger(name)
        logger.setLevel(level)

        # create console handler and set level to debug
        handler = StreamHandler()
        handler.setLevel(level)

        # create formatter
        formatter = Formatter('%(asctime)s %(levelname)s %(process)s --- [%(threadName)s] %(filename)s.%(name)s.%(funcName)s().%(lineno)d: %(message)s')

        # add formatter to handler
        handler.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(handler)
        return logger

    @staticmethod
    def create_logger(name='mixed', configuration_file='logger.conf'):
        try:
            fileConfig(configuration_file)
            return getLogger(name)
        except Exception as e:
            console_logger = LoggerFactory.create_console_logger(name)
            console_logger.warn("Couldn't create logger with configuration %s - Exception(%s).", configuration_file, e)
            return console_logger
