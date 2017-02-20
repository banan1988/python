import logging
import os
import signal
import time
from subprocess import Popen, PIPE, TimeoutExpired, CalledProcessError

__version__ = "0.1"

__all__ = ["Command"]


class Command:
    pid = -1
    return_code = None
    stdout = None
    stderr = None
    stop = False
    retry_attempt = 0

    def __init__(self, command, timeout=None, shell=False):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.command = command
        self.timeout = timeout
        self.shell = shell

        self.proc = None

        signal.signal(signal.SIGTERM, self.handler)

    def __str__(self):
        return "Command(" \
               "pid=%s, " \
               "command=%s, " \
               "return_code=%s, " \
               "stdout=%s, " \
               "stderr=%s)" % (
                   self.pid,
                   self.command,
                   self.return_code,
                   self.stdout,
                   self.stderr
               )

    def execute(self):
        try:
            with Popen(self.command, stdout=PIPE, stderr=PIPE, shell=self.shell) as self.proc:
                self.pid = self._pid()
                self.logger.error("[%s] Started command - %s" % (self.pid, self.command))
                while True:
                    if self.proc.poll() is not None or self.stop:
                        break
                    else:
                        time.sleep(0.1)

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

    def _pid(self):
        if self.proc:
            return self.proc.pid
        return -1

    def terminate(self):
        try:
            if self.proc:
                self.proc.terminate()
        except PermissionError:
            if self._log():
                self.logger.error("[%s] Terminate operation is not permitted - %s." % (self.pid, self.command), exc_info=False)
            try:
                if self.proc:
                    self.proc.kill()
            except PermissionError:
                if self._log():
                    self.logger.error("[%s] Kill operation is not permitted - %s." % (self.pid, self.command), exc_info=False)
                self._terminate_as_root()
        except ProcessLookupError:
            self.logger.error("[%s] Not found an open process which executes - %s." % (self.pid, self.command), exc_info=False)
            pass

    def _terminate_as_root(self):
        try:
            sudo_kill = "sudo kill %s" % self.pid
            result = os.system(sudo_kill)
            if self._log():
                self.logger.error("[%s] Executed command %s returns %s" % (self.retry_attempt, sudo_kill, result))
            self._wait_for_stop()

            if self.retry_attempt >= 600:
                raise Exception("Stopping is taking too much time")

            os.killpg(os.getpgid(self.pid), signal.SIGTERM)
        except Exception as e:
            self.logger.error("[%s][STACKED] Couldn't kill an open process as a root - %s" % (self.pid, e))

    def _wait_for_stop(self):
        if self.proc:
            for i in range(10):
                if self.proc.poll() is not None:
                    exit(self.proc.poll())
                # self.logger.error("[%d] Still working: %s" % (i, self.proc.poll()))
                time.sleep(0.01)

    def handler(self, signum, frame):
        self.retry_attempt += 1
        if self._log():
            self.logger.error("[%s] Handle signal - %s (SIGTERM=15)" % (self.pid, signum))
        self.terminate()
        self.stop = True

    def _log(self):
        return self.retry_attempt == 1 or self.retry_attempt % 30 == 0

if __name__ == '__main__':
    c = None
    try:
        cmd = "sudo ./gor --input-raw :8080 --http-allow-url /a1 --output-http http://c.host.domain.com:8080|100%"
        c = Command(cmd.split(" "))
        result = c.execute()
        print("# result", result)
    except SystemExit as e:
        print("# SystemExit", e)
    except Exception as e:
        print("# Exception", e)
    finally:
        print("# Finally terminate")
        c.terminate()
