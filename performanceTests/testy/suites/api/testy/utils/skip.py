import pytest
from os import getenv

skip_if_cloudant_local = pytest.mark.skipif(
    'pytest.config.getoption("TESTY_CLOUDANT_CONTEXT") == "cloudant_local"',
    reason="not a valid test for Cloudant Local")

skip_if_jenkins = pytest.mark.skipif(
    getenv("TESTY_JENKINS_RUN", False) != False,
    reason="Skipping - test not suitable for Jenkins"
    )

skip_if_not_testy = pytest.mark.skipif(
    "testy" not in pytest.config.getoption("TESTY_CLUSTER"),
    reason="not a test cluster")


def xfail_if_dbnext(reason):
    return pytest.mark.xfail(not pytest.config.getoption("TESTY_CLOUDANT_CONTEXT") == 'SAAS',
                             reason=reason)
