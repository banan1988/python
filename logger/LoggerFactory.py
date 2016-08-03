from logging import getLogger, Formatter, StreamHandler, DEBUG
from logging.config import fileConfig


class LoggerFactory:
    def __init__(self):
        pass

    @staticmethod
    def __create_console_logger(name, level=DEBUG):
        # create logger
        logger = getLogger(name)
        logger.setLevel(level)

        # create console handler and set level to debug
        handler = StreamHandler()
        handler.setLevel(level)

        # create formatter
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to handler
        handler.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(handler)
        return logger

    @staticmethod
    def create_logger(name, configuration_file='example_logger.conf'):
        try:
            fileConfig(configuration_file)
            return getLogger(name)
        except Exception as e:
            print ("Couldn't create logger using %s" % configuration_file, e)
            return LoggerFactory.__create_console_logger(name)
