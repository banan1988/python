import logging

from subprocess import Popen, PIPE, TimeoutExpired, CalledProcessError

__version__ = "0.1"

__all__ = ["Command"]


class Command:
    pid = -1
    return_code = 0
    stdout = None
    stderr = None

    def __init__(self, command, timeout=None, shell=False):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.command = command
        self.timeout = timeout
        self.shell = shell

        self.proc = None

    def __str__(self):
        return "Command(" \
               "command=%s, " \
               "return_code=%d, " \
               "stdout=%s, " \
               "stderr=%s)" % (
                   self.command,
                   self.return_code,
                   self.stdout,
                   self.stderr
               )

    def execute(self):
        try:
            with Popen(self.command, stdout=PIPE, stderr=PIPE, shell=self.shell) as self.proc:
                self.pid = self._pid()
                self.proc.wait(self.timeout)

                self.return_code = self.proc.returncode
                self.stdout = self.proc.stdout.read().decode('utf-8').strip()
                self.stderr = self.proc.stderr.read().decode('utf-8').strip()

                return self
        except TimeoutExpired as e:
            raise e
        except CalledProcessError as e:
            raise e
        except Exception as e:
            raise e

    def terminate(self):
        try:
            if self.proc and not self.proc.poll():
                self.proc.terminate()
        except PermissionError:
            self.logger.error("[%s] Process already died - %s." % (self.proc.pid, self.command), exc_info=False)
            pass
        except ProcessLookupError:
            self.logger.error("[%s] Not found an open process which executes - %s." % (self.proc.pid, self.command), exc_info=False)
            pass

    def _pid(self):
        if self.proc:
            return self.proc.pid
        return -1
