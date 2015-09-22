#  conftest.py
#  -----------
#
#  For extending the default pytest functionality to allow
#  the running of tests in languages other than Python.
#

import pytest
import os
import os.path
import uuid
from pytest_pep8 import Pep8Item
from testy.pretest import setup_test
from testy.posttest import process_result, tmp_dir_cleanup
from testy.shell import ShellScriptFile, ShellScriptTestItem


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    """
    Test post-processing. Execute all other hooks to obtain the report object,
    save it to a database, and then do any other post-test cleanup.
    """
    rep = __multicall__.execute()

    if rep.when == "call" and not rep.skipped:
        process_result(rep, item)
        tmp_dir_cleanup(item)

    return rep


@pytest.mark.tryfirst
def pytest_runtest_setup(item):
    """
    Shell script tests need to have their env set up early
    """
    if isinstance(item, ShellScriptTestItem):
        setup_test(item)


@pytest.mark.tryfirst
def pytest_runtest_call(item):
    """
    Python tests need to have their env setup when they are called
    """
    if isinstance(item, ShellScriptTestItem) or isinstance(item, Pep8Item):
        return

    setup_test(item)
    if isinstance(item, pytest.Function) and not hasattr(item.obj, "im_class"):
        item.obj.func_globals['_env'] = item.config.env
    else:
        instance = item.obj.im_self
        instance._env = item.config.env


def pytest_addoption(parser):
    """
    Let pytest know about our configuration file.
    """
    group = parser.getgroup(
        name='testy options',
        description='testy subcommands',
    )

    testy_options = [
        (
            'TESTY_CLOUDANT_CONTEXT',
            'Defaults to SAAS, use cloudant_local for running testy'
            'against Cloudant local or a VM with port forwarding',
            'SAAS'
        ),
        ('TESTY_CLUSTER', 'Cluster to test, e.g. `testy001`', ''),
        (
            'TESTY_CLUSTER_LB',
            'Comma-separated list of load balancers (e.g. `lb1,lb2`)',
            ''
        ),
        (
            'TESTY_CLUSTER_NODENAMES',
            'Comma-separated list of cluster nodes (e.g. `db1,db2,db3`)',
            ''
        ),
        (
            'TESTY_CLUSTER_URL',
            'URL of the cluster (e.g. `https://testy001.cloudant.com`)',
            ''
        ),
        ('TESTY_DB_ADMIN_PASS', 'password for admin account', ''),
        (
            'TESTY_DB_ADMIN_ROOT',
            'Root URL of account with admin permissions '
            '(e.g. `https://testy001-admin.cloudant.com`)',
            ''
        ),
        (
            'TESTY_DB_ADMIN_USER',
            'username of account with admin permissions',
            ''
        ),
        (
            'TESTY_DB_NAME',
            'name of test database (auto-generated if unspecified)',
            ''
        ),
        ('TESTY_DB_READ_PASS', 'password for read-only account', ''),
        ('TESTY_DB_READ_USER', 'username for read-only account', ''),
        (
            'TESTY_DB_URL',
            'URL of database to use in the test. Generated from '
            'TESTY_DB_ADMIN_ROOT and TESTY_DB_NAME if unspecified.',
            ''
        ),
        ('TESTY_DB_WRITE_PASS', 'password for write-only account', ''),
        ('TESTY_DB_WRITE_USER', 'username for write-only account', ''),
        (
            'TESTY_NO_CLEAN_TMP',
            "Don't delete any new files/directories created in TESTY_TMP_DIR "
            "after the test has finished running",
            False
        ),
        (
            'TESTY_RESULT_DIR',
            'full path to local directory for test results (auto-generated if '
            'unspecified)',
            ''
        ),
        (
            'TESTY_SAVE_PASS',
            'password of the account to write test results with',
            ''
        ),
        ('TESTY_SAVE_URL', 'URL to write test results to', ''),
        (
            'TESTY_SAVE_USER',
            'username of the account to write test results with',
            ''
        ),
        ('TESTY_TMP_DIR', 'temp directory to use', '`pwd`/tmp'),
        ('TESTY_USE_REPLICATOR_DB',
         'Testy defaults to the _replicate endpoint for all replication tests '
         'set to this flag and testy will use the _replicator db.',
         False),
        ('TESTY_REPLICATE_WITH_HTTPS',
         'Testy generates URLs for replications which by default use https '
         'set this flag to false and testy will use http in the non-SAAS context.',
         True),
        ('TESTY_REPLICATION_HOST',
         'Manually specify a host for replication URLs rather than having testy '
         'create one from the db_admin_root. This is useful if the external '
         'hostname of the load balancer is different to the internal hostname '
         '(e.g. if you are running against a containerized cluster.',
         None),
        ('TESTY_REPLICATION_PORT',
         'Manually specify a port for replication URLs. See TESTY_REPLICATION_HOST.',
         None)
    ]
    for test_opt in testy_options:
        if test_opt[2] is True:
            action = 'store_false'
        elif test_opt[2] is False:
            action = 'store_true'
        else:
            action = 'store'
        group.addoption(
            '--%s' % test_opt[0].replace('TESTY_', ''). lower(),
            dest=test_opt[0],
            default=test_opt[2],
            action=action,
            help=test_opt[1]
        )

    group.addoption(
        '--skip_teardown',
        help='set this flag and the testy dbs will not be deleted on tear down',
        default=False,
        action='store_true'
    )
    group.addoption(
        '--runid',
        help='Set an id for the test run',
        default=str(uuid.uuid1())
    )
    group.addoption(
        '--output',
        help='Write test results into OUTPUT',
        default=os.path.join(os.getcwd(), 'testy_results')
    )
    group.addoption(
        '--comment',
        help='Additional comment to be written into the database',
        default=''
    )
    group.addoption(
        '--overrides',
        help='JSON file containing additional environment variables and ' +
        'parameters for tests (overriding those set at group or test level)',
    )


def pytest_collect_file(parent, path):
    """
    Add language matchers here that will return an object derived from
    pytest.File that can collect tests from the matched files
    """

    if path.ext == ".sh" and path.basename.startswith("test"):
        return ShellScriptFile(path, parent)
