Testy
=====

Test harness for integration, regression, API and load testing, etc.

> "Everyone knows that debugging is twice as hard as writing a program in the first place. So if you’re as clever as you can be when you write it, how will you ever debug it?"

_Brian Kernighan_

## Booking and using test clusters

Please [see the wiki](https://github.com/cloudant/testy/wiki) for details of how to do this.

## Using the Testy test-harness

Create a virtual environment for testy:

    virtualenv venv
    source venv/bin/activate

Install requirements:

    pip install -r requirements.txt


## Running tests

A simple example to run the API tests against a standard Cloudant DBaaS account:

    ./runtesty.py --db_admin_user=USERNAME --db_admin_pass=PASSWORD --db_admin_root=http://USERNAME.cloudant.com suites/api/

Or, if you want to run the standard set of "fast" acceptance tests (takes about 20 minutes), then do:

    ./runtesty.py --db_admin_user=USERNAME --db_admin_pass=PASSWORD --db_admin_root=http://USERNAME.cloudant.com -f suites/standard_suite_fast.json

Here is an example for running the tests against a Cloudant Local cluster - note the `--cloudant_context` option:

    ./runtesty.py -f suites/standard_suite_fast.json --timeout=100 --cloudant_context=cloudant_local --db_admin_user=adm-testing --db_admin_pass=PASSWORD --db_admin_root=https://cloudantlocal3.cloudant.com

Much more is possible - see `./runtesty.py -h`.

The various different tests suites are all under the suites directory.  The test harness is capable of running shell-script tests and python tests of the form:

    test_*.sh
    test_*.py

## Writing tests

Write tests in either shell-script form or in Python.  Generally best to write Python tests that somehow derive from python unittest:TestCase, although simpler forms of python tests are possible.  See the `suites/demo` directory for various examples.
