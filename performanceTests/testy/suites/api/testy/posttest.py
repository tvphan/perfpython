import requests
import json
import datetime
from os.path import join, isfile
from os import listdir, removedirs
from utils import make_db, delete_file_ignore_errors
from collections import defaultdict
from functools import partial
from shutil import rmtree
from pytest_pep8 import Pep8Item


def save_creds(item):
    auth = ()
    save_user = item.config.env.get('TESTY_SAVE_USER')
    save_pass = item.config.env.get('TESTY_SAVE_PASS')
    save_url = item.config.env.get('TESTY_SAVE_URL')
    if save_user and save_pass:
        auth = (save_user, save_pass)

    return save_url, auth


def build_report_doc(result, json_output, item):
    """
    Build the report doc and write it to the database
    """
    # TODO: decide what to store and store it
    test_report = defaultdict(dict)

    test_report.update(
        {
            "test": result.nodeid,
            "passed": result.passed,
            "script": item.name,
            "comment": str(item.config.option.comment),
            "duration": result.duration,
            "date_ran": tuple(datetime.datetime.utcnow().timetuple()),
            "run_id": str(item.config.option.runid),
        }
    )

    save_url, auth = save_creds(item)

    result_dir = item.config.env.get('TESTY_RESULT_DIR')

    excludes = []

    for var in item.config.env.keys():
        if 'PASS' or 'DIR' not in var:
            test_report['env'][var] = item.config.env.get(var)

    for j in json_output:
        # read the json, insert to the test_report
        key = j.split('.')[0]
        test_report['results'][key] = {}
        with open(join(result_dir, j)) as f:
            # TODO: deal with bad json
            test_report['results'][key] = json.load(f)

    doc = requests.post(
        save_url,
        data=json.dumps(test_report),
        headers={'content-type': 'application/json'},
        auth=auth,
    ).json()

    # TODO: do some error handling here
    print 'store:', doc
    return doc


def attach_files(doc, files, item):
    """
    Attach test output files that aren't json to the report doc
    """
    result_dir = item.config.env.get('TESTY_RESULT_DIR')

    save_url, auth = save_creds(item)

    for result_file in files:
        if not result_file.endswith('.json'):
            result_file_path = join(
                result_dir,
                result_file
            )
            with open(result_file_path) as f:
                doc = requests.put(
                    '/'.join([
                        save_url,
                        doc['id'],
                        result_file,
                    ]),
                    files={result_file_path: f},
                    params={'rev': doc['rev']},
                    auth=auth,
                )
                # TODO: some error handling/reporting


def result_files(item):
    result_dir = item.config.env.get('TESTY_RESULT_DIR')
    files = listdir(result_dir)
    json_files = [f for f in files if f.endswith('.json')]
    return files, json_files


def process_result(rep, item):
    """
    Process the test result and store to a DB (if so configured).
    """
    if item.config.option.TESTY_SAVE_URL:
        make_db(item)

        files, json_files = result_files(item)

        doc = build_report_doc(rep, json_files, item)

        attach_files(doc, files, item)


def tmp_dir_cleanup(item):
    """
    Do any post-test cleanup of TESTY_TMP_DIR, if necessary.
    """
    # PEP8 does very weird things
    if isinstance(item, Pep8Item):
        return

    if not item.config.env["TESTY_NO_CLEAN_TMP"]:
        tmpdir = item.config.env["TESTY_TMP_DIR"]
        ls_before = set(item.testy_tmp_dir_ls_before)
        ls_after = set(listdir(tmpdir))
        deletable = ls_after - ls_before
        # Append the tmpdir path to each deletable entry
        # Bah! No set comprehensions in python 2.6. Nasty hacks required.
        deletable = set([join(tmpdir, entry) for entry in list(deletable)])
        # Separate the files and directories
        files = set([path for path in list(deletable) if isfile(path)])
        dirs = deletable - files
        # Delete the files and directories, ignoring any errors.
        map(delete_file_ignore_errors, files)
        map(partial(rmtree, ignore_errors=True), dirs)

        # If the directory was empty before, then prune back the
        # tmpdir path until we hit a dir with files in.
        if not ls_before:
            try:
                removedirs(tmpdir)
            except:
                pass
