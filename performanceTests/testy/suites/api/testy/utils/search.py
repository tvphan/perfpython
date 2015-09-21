import pytest
import subprocess

__all__ = ["skip_if_clouseau_unavailable"]

_clouseau_running_check_result = None  # Cached result from the check.


def _is_clouseau_running():
    """
    Determine whether clouseau is running, using epmd.

    If epmd fails, assume it's not running.
    """
    global _clouseau_running_check_result
    if _clouseau_running_check_result is not None:
        return _clouseau_running_check_result
    is_running = False
    try:
        p = subprocess.Popen(["epmd", "-names"], stdout=subprocess.PIPE)
        is_running = any(line.startswith("name clouseau") for line in p.stdout)
        p.wait()
    except OSError, e:
        pass
    _clouseau_running_check_result = is_running
    return is_running

skip_if_clouseau_unavailable = pytest.mark.skipif(
    "not __import__('testy.utils.search', "
    "               fromlist=['search'])._is_clouseau_running()",
    reason="clouseau isn't running (or epmd couldn't be found)")
