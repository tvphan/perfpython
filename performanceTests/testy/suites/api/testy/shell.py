import pytest
import os
import subprocess


# Shell-script test-running specialisation classes
class ShellScriptFile(pytest.File):
    """Shell-script test-collector class"""
    def collect(self):
        """
        Collects and yields the test(s); must yield items in the form of a
        class derived from pytest.Item
        """

        # For shell-scripts, the test 'collection' step is trivial. The test
        # is just the file itself; there is no need to examine the file
        # content.
        pathstr = self.fspath.strpath  # Get the path in string form
        yield ShellScriptTestItem(self.name, self, pathstr)


class ShellScriptTestItem(pytest.Item):
    """
    Encapsulates the code required to run and report on a shell-script test
    """

    def __init__(self, name, parent, pathstr):
        super(ShellScriptTestItem, self).__init__(name, parent)
        self.pathstr = pathstr  # Path in string form

        if not os.access(self.pathstr, os.X_OK):
            raise ShellScriptTestException('%s not executable' % self.pathstr)

    def runtest(self):
        """Test runner - must raise a custom exception type on test failure"""

        env = {}
        env.update(os.environ)
        env.update(self.config.env)

        # subprocess requires all env to be strings
        for k, v in env.items():
            env[k] = str(v)

        try:
            return_code = subprocess.call(
                [self.pathstr] + self.config.parameters,
                env=env
            )
        except Exception as err:
            # Most likely cause is pytest timeout killing the shell script
            print "Exception whilst running the shell script:", err
            return_code = 504  # Gateway timeout err code seemed appropriate...

        if return_code != 0:
            raise ShellScriptTestException(self, self.name, return_code)

    def repr_failure(self, excinfo):
        """This is called when self.runtest() raises an exception"""

        if isinstance(excinfo.value, ShellScriptTestException):
            testname, return_code = excinfo.value.args[1:3]
            response = "\nThe test '%s' failed with non-zero error code %s" \
                % (testname, return_code)
            return response

    def reportinfo(self):
        """
        Output of this function is used in the title of the test failure report
        """

        return self.fspath, 0, "shell-script: %s" % self.name


class ShellScriptTestException(Exception):
    """Custom exception for shell-script test failures"""
