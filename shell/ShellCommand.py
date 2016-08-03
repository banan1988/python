from subprocess import Popen, PIPE, CalledProcessError


class ShellCommand:
    returncode = 0
    stdout = None
    stderr = None

    def __init__(self, command):
        self.command = command

    def __str__(self):
        return "ShellCommand(" \
               "command=%s, " \
               "returncode=%d, " \
               "stdout=%s, " \
               "stderr=%s)" % (
                   self.command,
                   self.returncode,
                   self.stdout,
                   self.stderr
               )

    def execute(self):
        p = None
        try:
            p = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True)
            p.wait()

            self.returncode = p.returncode
            self.stdout = p.stdout.read().decode('utf-8').strip()
            self.stderr = p.stderr.read().decode('utf-8').strip()
            return self
        except CalledProcessError as e:
            raise Exception("Couldn't execute command: %s - %s" % (self.command, e.output))
        except Exception as e:
            raise Exception("Couldn't execute command: %s - %s" % (self.command, e))
        finally:
            if p:
                try:
                    p.kill()
                except OSError:
                    pass
