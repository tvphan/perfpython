from hamcrest import assert_that, is_, is_in
from urlparse import urlparse
import ConfigParser
import os
import requests
import json
import pytest
import string
import random
import time


def post_replication(source, targetdb, auth, options={}, **kwargs):
    """
    **kwargs:
    :param str root_url: e.g. "TESTY_DB_ADMIN_ROOT".
    :param str context: e.g. "TESTY_CLOUDANT_CONTEXT".
    :param dict options: replication options e.g. {"creat_target": True}.

    :param tuple auth: e.g. (user, pass).
    :param str source: The replication source. pass a examples.cloudant.com db
    name.  Nonetheless, if you specify a url for the source parameter, it will use it.
    """
    root = kwargs.get('root_url', '')
    target = create_target_url(targetdb, auth, root, kwargs.get('context', ''))
    source_url = check_source_url(source, auth, root)
    repdoc_base = {"source": source_url,
                   "target": target}
    repdoc = dict(repdoc_base.items() + options.items())

    if pytest.config.getoption('TESTY_USE_REPLICATOR_DB'):
        create_replicator_db(auth, root)
        repdoc['_id'] = "testy_{0}".format(''.join(random.choice(string.ascii_uppercase) for i in range(4)))
        response = requests.post(root + "/_replicator",
                                 data=json.dumps(repdoc),
                                 headers={"Content-Type":
                                          "application/json"},
                                 auth=auth)
        return response
    else:
        response = requests.post(root + "/_replicate",
                                 data=json.dumps(repdoc),
                                 headers={"Content-Type":
                                          "application/json"},
                                 auth=auth)
        return response


def create_target_url(targetdb, auth, root, context):
    if context is 'SAAS':
        return "https://{0}:{1}@{0}.cloudant.com/{2}".format(auth[0],
                                                             auth[1],
                                                             targetdb)
    else:
        root_url = _get_replication_url(root)
        return "{0}://{1}:{2}@{3}/{4}".format(_protocol(),
                                              auth[0],
                                              auth[1],
                                              root_url,
                                              targetdb)


def check_source_url(source, auth, root):
    if source in ["animaldb",
                  "check",
                  "cookbook",
                  "crud",
                  "geo",
                  "lobby-search",
                  "movies-demo",
                  "nyctaxi",
                  "reformatting",
                  "sales",
                  "scores",
                  "simplegeo_places",
                  "user_profiles",
                  "whatwouldbiebersay"]:
        return "https://examples.cloudant.com/{0}".format(source)
    if "testy_db" in source:
        root_url = _get_replication_url(root)
        return "{0}://{1}:{2}@{3}/{4}".format(_protocol(),
                                              auth[0],
                                              auth[1],
                                              root_url,
                                              source)
    if "http" in source:
        return source
    else:
        raise NameError('Invalid source, it is eather a url or an' /
                        'examples db, e.g. "animaldb"')


def create_replicator_db(auth, root):
        replicator = requests.get(root + '/_replicator',
                                  auth=auth)

        if replicator.status_code is 200:
            return replicator
        else:
            response = requests.put(root + '/_replicator',
                                    auth=auth)
            assert_that(response.status_code, is_(accepted()))

            mark_for_delete = requests.put(root + '/_replicator/_local/delete_db',
                                           data=json.dumps({"testy": "delete_db"}),
                                           auth=auth)
            assert_that(mark_for_delete.status_code, is_(accepted()))
            return response


def put_animaldb(db_url, auth=()):
    with open('utils/format_checker/animaldb.json') as json_data:
        adb = json.load(json_data)

    requests.put(db_url, auth=auth)

    response = requests.post(db_url + "/_bulk_docs",
                             data=json.dumps(adb),
                             auth=auth,
                             headers={"Content-Type":
                                      "application/json"})
    assert_that(response.status_code, is_(accepted()))
    return response


def get_adm_creds():
# Get creds from the users local .clou config file
        conf = ConfigParser.ConfigParser()
        conf.read(os.path.expanduser('~/.clou'))
        creds = (
            conf.get('cloudant', 'adm_user'),
            conf.get('cloudant', 'adm_password'),
        )
        return creds


def remove_replicator_docs(root, auth=()):
    rep_url = root + "/_replicator/{0}"
    all_docs = requests.get(root + "/_replicator/_all_docs",
                            auth=auth,
                            params={"startkey": json.dumps("testy_"),
                                    "endkey": json.dumps("testy_ZZZZ")})

    if 'rows' in all_docs.json():
        for rep_id in all_docs.json()['rows']:
            if "testy" in rep_id['id']:
                rev = requests.get(rep_url.format(rep_id['id']),
                                   auth=auth)
                requests.delete(rep_url.format(rep_id['id']),
                                params={"rev": rev.json()['_rev']},
                                auth=auth)

    mark_for_delete = requests.get(root + '/_replicator/_local/delete_db',
                                   auth=auth)
    if mark_for_delete.status_code == 200:
        response = requests.delete(root + '/_replicator',
                                   auth=auth)
        assert_that(response.status_code, is_(accepted()))


def check_replication_state(root, _id, auth=(), timeout=75, state="completed"):
        sleep_time = timeout / 10
        for i in range(10):
            time.sleep(sleep_time)
            response = requests.get(root +
                                    "/_replicator/{0}".format(_id),
                                    auth=auth)
            if "_replication_state" in response.json().keys():
                if response.json()['_replication_state'] == state:
                    return True
            else:
                pass
        return False


def get_option(option_name):
    return pytest.config.getoption(option_name)


def skipp_taredown():
    return get_option('--skip_teardown')


def check_accepted(response):
    assert_that(response.status_code, is_(accepted()))
    return response


def accepted():
    return is_in([200, 201, 202, {"result": "created"}])


def not_found():
    return is_(404)


def bad_request():
    return is_(400)


def forbidden():
    return is_in([403, 401])


def conflict():
    return is_(409)


def precondition_failed():
    return is_(412)


def _protocol():
    if pytest.config.getoption('TESTY_REPLICATE_WITH_HTTPS'):
        return 'https'
    else:
        return 'http'

def _get_replication_url(root):
    if pytest.config.getoption('TESTY_REPLICATION_HOST') and \
            pytest.config.getoption('TESTY_REPLICATION_PORT'):
        return '{0}:{1}'.format(
            pytest.config.getoption('TESTY_REPLICATION_HOST'),
            pytest.config.getoption('TESTY_REPLICATION_PORT')
        )
    else:
        return urlparse(root)[1]
