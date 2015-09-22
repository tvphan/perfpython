#!/usr/bin/env python

import pytest
import sys
import os.path
import json
import shutil
from itertools import chain
from argparse import ArgumentParser, Action, FileType, _ensure_value


# The sub-directory to all the various user test suites
TEST_SUITES_DIR = "suites"

# The sub-directory for Testy's self-tests
TESTY_SELF_TESTS_DIR = "testy_tests"


class ConfigAction(Action):
    """
    Given a json file ConfigAction will populate the parser with properties
    defined in the json. This won't override settings from other actions or
    allow settings not defined in the parser initialisation.
    """

    def __init__(self,
                 option_strings,
                 dest,
                 default=None,
                 required=False,
                 help=None):
        super(ConfigAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=1,
            default=default,
            type=FileType('r'),
            required=required,
            help=help,
            metavar='FILE')

    def __call__(self, parser, namespace, values, option_string=None):
        cfg_values = {}
        for i in values:
            cfg_values.update(json.load(i))
        for k, v in cfg_values.items():
            if parser.get_default(k) == _ensure_value(namespace, k, v):
                setattr(namespace, k, v)


def get_options():
    """
    Get options via argparse and return them in a format pytest will like
    """
    parser = ArgumentParser(description='Run some tests.', add_help=False)
    parser.register('action', 'config', ConfigAction)
    parser.add_argument(
        'test',
        metavar='TEST',
        nargs='*',
        help='only run named test(s) ignoring any group, include or exclude'
    )
    parser.add_argument(
        '-g',
        '--group',
        action='append',
        default=[],
        help='group of tests (directory) to run'
    )
    parser.add_argument(
        '-e',
        '--exclude',
        action='append',
        default=[],
        metavar='TEST',
        help='exclude the named test (single file) from the group for the run'
    )
    parser.add_argument(
        '-i',
        '--include',
        action='append',
        default=[],
        metavar='TEST',
        help='include the named test (single file) in the run'
    )
    parser.add_argument(
        '-f',
        '--config',
        action='config',
        help='Read settings from json FILE'
    )
    parser.add_argument(
        '--dryrun',
        action='store_true',
        default=False,
        help='Find all the tests and set paramaters but do not run the tests'
    )
    parser.add_argument(
        '-h',
        '--help',
        action='store_true',
        default=False,
        help='Print the helpful help message'
    )
    default_output = os.path.join(os.getcwd(), 'testy_results')
    parser.add_argument(
        '-o',
        '--output',
        help='''Write test results into OUTPUT. Directory is deleted and
        recreated each run. Default is %s''' % default_output,
        default=default_output)

    return parser


def collect_tests(groups, excludes, includes):
    """
    Determine the set of tests to run from a list of groups, excludes and
    includes.
    """
    tests = []

    for paths in groups, excludes, includes:
        maybe_prepend_suites_dir(paths)

    for potential_test in chain(excludes, includes):
        if not os.path.isfile(potential_test):
            msg = '%s is not a file - includes/excludes only work for files'
            raise IOError(msg % potential_test)

    if len(excludes):
        for group in groups:
            files = ['%s/%s' % (group, x) for x in os.listdir(group)]
            files = filter(
                lambda x: os.path.splitext(x)[1] in ['.sh', '.py'],
                files
            )

            original_len = len(files)
            files = list(set(files) - set(excludes))
            if len(files) == original_len:
                tests.append(group)
            else:
                tests.extend(files)
    else:
        tests.extend(groups)

    tests = list(set(tests) | set(includes))
    return tests


def maybe_prepend_suites_dir(paths):
    """
    prepend the TEST_SUITES_DIR directory to the paths if needed.
    Prepending doesn't occur if the path already starts with
    TEST_SUITES_DIR, or if the path begins with Testy's own
    self-test directory.

    paths -- a list of path strings
    """
    # Directly modify the content of the list being passed in
    for ipath in range(len(paths)):
        if not (paths[ipath].startswith(TESTY_SELF_TESTS_DIR) or
                paths[ipath].startswith(TEST_SUITES_DIR)):
            paths[ipath] = os.path.join(TEST_SUITES_DIR, paths[ipath])


def build_arguments(options):
    """
    Build up the arguments for pytest. This will be:
     * the list of tests to run
     * any options we want to pass to pytest
    """

    arguments = []

    shutil.rmtree(options.output, ignore_errors=True)
    os.makedirs(options.output)

    print 'test output will be under %s' % options.output

    if options.test:
        arguments = collect_tests(
            options.test,
            options.exclude,
            options.include
        )
    else:
        arguments = collect_tests(
            options.group,
            options.exclude,
            options.include
        )

    return arguments


def parse_args(parser):
    """
    Get the testy options and the arguments to pass along to pytest,
    """
    options, unknown_args = parser.parse_known_args()

    destinations = [getattr(x, 'dest') for x in parser._actions]

    arguments = build_arguments(options)
    arguments.extend(unknown_args)

    for i in options._get_kwargs():
        if i[0] not in destinations:
            arguments.append("--%s" % i[0])
            if i[1]:
                arguments.append("%s" % i[1])

    return options, arguments


def main():
    parser = get_options()
    options, arguments = parse_args(parser)

    if options.dryrun:
        print arguments
        print "\n** Dry run - only collecting tests **\n"
        return pytest.main(arguments + ['--collectonly'])
    if options.help:
        parser.print_help()
        print '=' * 80
        return pytest.main(['--help'])
    else:
        return pytest.main(arguments)


if __name__ == '__main__':
    sys.exit(main())
