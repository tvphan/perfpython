import json
import os
import os.path
import time
from shell import ShellScriptTestItem
import posixpath
from random import choice
from string import ascii_lowercase


def get_settings_files(test):
    """
    Get the paths to both settings files we want from the test script location
    """
    test_filename, _ = os.path.splitext(test.fspath.strpath)
    group_dir, _ = os.path.split(test_filename)
    _, group_name = os.path.split(group_dir)
    group_filename = os.path.join(group_dir, 'test_%s' % group_name)

    return ['%s_settings.json' % x for x in [test_filename, group_filename]]


def get_settings(test):
    test_settings_path, group_settings_path = get_settings_files(test)
    settings = {
        test_settings_path: {},
        group_settings_path: {},
        test.config.option.__dict__.get('overrides'): {}
    }

    for k in settings.keys():
        try:
            with open(k) as f:
                settings[k] = json.load(f)
        # If f is invalid json json.load will raise a ValueError, which we then
        # reraise to communicate the problem
        except ValueError, e:
            raise e
        except:
            pass

    return settings[test_settings_path], \
        settings[group_settings_path], \
        settings[test.config.option.__dict__.get('overrides')]


def get_conditions_from_config_files(test):
    """
    Read group and test config files, return a tuple of parameters and envvars.
    """
    test_settings, group_settings, override_settings = get_settings(test)
    parameters = override_settings.get('parameters', [])

    if len(parameters) == 0:
        # If the test has params take those, otherwise get them from the group
        test_params = test_settings.get('parameters', [])
        if len(test_params) > 0:
            parameters = test_params
        else:
            parameters = group_settings.get('parameters', [])

    environment = {}
    environment.update(group_settings.get('environment', {}))
    # individual test settings override settings at group level
    environment.update(test_settings.get('environment', {}))
    # environment from the command line overrides config files
    environment.update(override_settings.get('environment', {}))

    return parameters, environment


def make_result_dir(item):
    """
    Create the result directory for the test item.
    """
    subdir_path = get_distinct_test_item_path(item)
    dir_name = os.path.join(item.config.option.output, subdir_path)
    os.makedirs(dir_name)
    return dir_name


def get_distinct_test_item_path(item):
    """
    Generate a relative result directory path that avoids clashes
    e.g. api/test_api/test_specific_feature.
    Note that for Python files that contain many individual test functions, the
    func name becomes part of the path in order to make it distinct from
    others.
    """
    if isinstance(item, ShellScriptTestItem):
        path, _ = os.path.splitext(item.name)
    else:  # Should be a Python test item
        test_dir, _ = os.path.splitext(item.location[0])
        path = os.path.join(test_dir, item.name)
    return path


def unique_db_name():
    """
    Create an unique test db name
    """
    result = "testy_db_"
    for i in range(10):
        result += choice(ascii_lowercase)
    return result


def testy_tmp_dir(path):
    """
    Returns a directory listing of the provided TESTY_TMP_DIR path. If the path
    doesn't exist, it creates it. If the path provided doesn't have adequate
    permissions for a valid tmp dir, an exception is thrown.
    """
    if os.access(path, os.F_OK):
        if os.access(path, os.R_OK | os.W_OK | os.X_OK):
            return os.listdir(path)
        else:
            raise Exception("TESTY_TMP_DIR directory `%s` exists but doesn't "
                            "have adequate permissions!" % path)
    else:
        os.makedirs(path, 0755)
        return []


def get_env_from_cli(item):
    """
    Get any enviroment passed in via the Command Line Interface
    """
    env = {}

    for k, v in item.config.option.__dict__.items():
        if k.startswith('TESTY_'):
            env[k] = v
        if k == 'TESTY_TMP_DIR' and v == '`pwd`/tmp':
            env[k] = os.path.join(os.getcwd(), "tmp")
            item.config.option.TESTY_TMP_DIR = env[k]

    return env


def autogenerate_missing_env(env, item):
    """
    Autogenerate various critical environment if not already set by any
    other means.  This function should be called *after* any other functions
    that read in or gather the environment somehow.
    """
    # Strip trailing / from URL's
    for key in ['TESTY_DB_URL', 'TESTY_DB_ADMIN_ROOT']:
        env[key] = env[key].strip('/')

    env['TESTY_TIMESTART'] = str(int(time.time()))

    # Generate a result output dir if none specified
    if not env['TESTY_RESULT_DIR']:
        env['TESTY_RESULT_DIR'] = make_result_dir(item)

    # If unspecified, generate a unique DB name from the test item path
    # and the start time.
    if not env['TESTY_DB_NAME']:
        env['TESTY_DB_NAME'] = unique_db_name()
    # Assume test DB URL is the admin root + db name, if unspecified
    if not env['TESTY_DB_URL']:
        env['TESTY_DB_URL'] = posixpath.join(env['TESTY_DB_ADMIN_ROOT'],
                                             env['TESTY_DB_NAME'])

    return env


def create_test_env(item):
    """
    Build the test environment/params for a given test item from the options
    passed in via the CLI, and also from any relevant config files.
    In particular, create the following TESTY env vars:
        TESTY_CLOUDANT_CONTEXT
        TESTY_CLUSTER
        TESTY_CLUSTER_LB
        TESTY_CLUSTER_NODENAMES
        TESTY_CLUSTER_URL
        TESTY_DB_ADMIN_PASS
        TESTY_DB_ADMIN_ROOT
        TESTY_DB_ADMIN_USER
        TESTY_DB_NAME
        TESTY_DB_READ_PASS
        TESTY_DB_READ_USER
        TESTY_DB_URL
        TESTY_DB_WRITE_PASS
        TESTY_DB_WRITE_USER
        TESTY_NO_CLEAN_TMP
        TESTY_RESULT_DIR
        TESTY_SAVE_PASS
        TESTY_SAVE_URL
        TESTY_SAVE_USER
        TESTY_TIMESTART
        TESTY_TMP_DIR
    """
    env = get_env_from_cli(item)
    parameters, cfg_env = get_conditions_from_config_files(item)
    env.update(cfg_env)
    env.update(autogenerate_missing_env(env, item))

    return parameters, env


def setup_test(item):
    """
    For a given test item, setup everything needed for the test to run.
    """
    # Get test parameters and environment
    parameters, env = create_test_env(item)

    # Setup the temp directory, and record a pre-test directory listing
    # so as not to delete these files on cleanup.
    item.testy_tmp_dir_ls_before = testy_tmp_dir(env['TESTY_TMP_DIR'])

    item.config.env = env
    item.config.parameters = parameters
