import json
import requests
import hashlib
import random
from string import digits, ascii_lowercase, ascii_uppercase
from auth import get_adm_creds


_ALPHABET = "".join([digits, ascii_lowercase, ascii_uppercase])


def replicate_testy_users_db_to_test_cluster(clustername):
    """
    Replicates the standard testy users database to the specified test cluster

    The standard testy users db includes the '-admin' test user for each of the
    test clusters (e.g. the testy001-admin user, etc)
    """
    _check_testy_cluster(clustername)
    session = _get_session()
    user, password = get_adm_creds()
    session.put("https://{0}.cloudant.com/users".format(clustername),
                params={'q': 1})
    data = {
        "source": "https://{0}:{1}@testy.cloudant.com/testy_users_db".format(
            user, password),
        "target": "https://{0}:{1}@{2}.cloudant.com/users".format(
            user, password, clustername),
        "create_target": True
    }
    response = session.post("https://testy.cloudant.com/_replicate",
                            data=json.dumps(data))
    response.raise_for_status()
    print "Testy users db replicated to {0} successfully!".format(clustername)


def create_many_users(clustername,
                      password,
                      num_users=100,
                      username_root="temp_user_"):
    """
    Create many (temporary) numbered users on a cluster with the same password
    """
    _check_testy_cluster(clustername)
    session = _get_session()
    url = _users_db_url(clustername) + "/_bulk_docs"
    user_docs = []
    for iuser in xrange(1, num_users + 1):
        username = "{0}{1}".format(username_root, iuser)
        print "Creating user doc for user:", username
        user_docs.append(generate_user_doc(username, password))
    response = session.post(url, data=json.dumps({"docs": user_docs}))
    response.raise_for_status()
    for result in response.json():
        if "error" in result:
            print "\nextError(s) found in per-document responses:"
            print response.json()
            raise Exception("Bulk upload errored on one or more user docs!")
    print "Created", num_users, "users successfully"


def create_single_user(clustername, username, password, roles=[]):
    """
    Creates a single (temporary) user on the given cluster

    Note that this doesn't create any DNS entries, etc. To interact
    with the created user you must use 'clustername.cloudant.com' in the
    URL and set the username via the X-Cloudant-User header
    """
    _check_testy_cluster(clustername)
    session = _get_session()
    url = _users_db_url(clustername)
    user_doc = generate_user_doc(username, password, roles)
    response = session.post(url, data=json.dumps(user_doc))
    response.raise_for_status()


def get_user(clustername, username):
    url = _users_db_url(clustername) + "/" + username
    session = _get_session()
    user = session.get(url)

    return user


def check_user_exist(clustername, username):
    user_doc = get_user(clustername, username).json()
    if '_id' in user_doc:
        return True
    else:
        return False


def delete_user(clustername, username):
    user_doc = get_user(clustername, username).json()
    url = _users_db_url(clustername) + "/" + \
        username + "?rev={0}".format(user_doc['_rev'])
    response = requests.delete(url, auth=get_adm_creds())
    response.raise_for_status()


def generate_user_doc(username, password, roles=[]):
    hasher = hashlib.sha1()

    salt = ''.join(random.choice(_ALPHABET) for i in range(16))
    hasher.update(password)
    hasher.update(salt)
    password_sha = hasher.hexdigest()
    doc = {
        "_id": username,
        "active": True,
        "email": "rob.frazier@cloudant.com",
        "password_sha": password_sha,
        "roles": roles,
        "salt": salt,
        "type": "user",
        "username": username
    }
    return doc


def _check_testy_cluster(clustername):
    if not clustername.startswith("testy"):
        raise Exception("Cowardly refusing to do anything to a "
                        "non-Testy cluster!")


def _get_session():
    session = requests.Session()
    session.auth = get_adm_creds()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    return session


def _users_db_url(clustername):
    return "https://{0}.cloudant.com/users".format(clustername)
