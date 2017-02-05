import argparse
import json
import logging
import os
import signal
import threading
from logging import basicConfig
from logging.config import dictConfig

from command import Command
from configuration import Configuration, ConfigurationReader
from gor import GorArgs

__version__ = "0.1"

__all__ = ["Cloner"]


class Cloner:
    def __init__(self, configuration: Configuration):
        self._register_system_stop()

        self.cloner_thread = None

        gor_args = GorArgs(configuration).get()
        self.gor_command = Command(gor_args)

        self.running = True

    def start(self):
        self.cloner_thread = threading.Thread(
            name="ClonerThread",
            target=self.gor_command.execute,
            daemon=True
        )
        self.cloner_thread.start()

    def wait_for_thread(self):
        while self.running and self.cloner_thread.is_alive():
            self.cloner_thread.join(timeout=1)

    def stop(self):
        self.gor_command.terminate()
        self.cloner_thread.join()

    def force_stop(self):
        os.kill(self.gor_command.pid, signal.SIGKILL)

    def details(self):
        if self.gor_command:
            return " ".join(self.gor_command.command)
        return None

    @staticmethod
    def version():
        gor_args = GorArgs(None, as_root=False).get()
        result = Command(gor_args).execute()
        version = result.stdout
        return version

    def _system_stop(self, signal, frame):
        self.running = False

    def _register_system_stop(self):
        # signal.signal(signal.SIGINT, self._system_stop)
        signal.signal(signal.SIGTERM, self._system_stop)


def get_args():
    parser = argparse.ArgumentParser(
        description='Cloner',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--version', action='store_true')
    parser.add_argument('--configuration-path', type=str,
                        required=False,
                        help='Path to configuration.')
    return parser.parse_args()


def setup_logging(
        path='logging.json',
        default_level=logging.INFO
):
    """
    Setup logging configuration
    """
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        dictConfig(config)
    else:
        basicConfig(level=default_level)


def stop(cloner):
    if cloner:
        try:
            cloner.stop()
            logging.info("[STOP] Stopped cloner - %s" % cloner.details())
        except Exception as e:
            logging.error("[STOP] Couldn't stop cloner(%s) normally: %s." % (cloner.details(), e))
            try:
                cloner.force_stop()
                logging.info("[FORCED STOP] Stopped cloner by force - %s" % cloner.details())
            except Exception as e:
                logging.error("[FORCED STOP] Couldn't stop cloner(%s) by force: %s." % (cloner.details(), e))


if __name__ == '__main__':
    setup_logging()
    args = get_args()

    if args.version:
        print(Cloner.version())
        exit(0)

    if not args.configuration_path or len(args.configuration_path) <= 0:
        raise Exception("--configuration-path argument is required !")

    cloner = None
    try:
        configuration = ConfigurationReader.read(args.configuration_path)

        cloner = Cloner(configuration)
        logging.info("[START] Started cloner - %s" % cloner.details())
        cloner.start()
        cloner.wait_for_thread()
    except SystemExit:
        logging.error('System exit', exc_info=True)
        pass
    except KeyboardInterrupt:
        logging.error('Keyboard interrupt', exc_info=False)
        pass
    except Exception as e:
        logging.error('Error', exc_info=True)
        raise
    finally:
        stop(cloner)
