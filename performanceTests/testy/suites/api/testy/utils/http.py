import requests
from functools import wraps
import unittest
from hamcrest import assert_that, is_, is_in, instance_of, is_not, has_key


def setup_session(f):
    """
    Helper function to decorate the setUp of a unittest.TestCase to create a
    requests session for the test to use.

    http://docs.python-requests.org/en/latest/user/advanced/#session-objects
    """
    @wraps(f)
    def decorator(test):
        """
        Decorator should only be called on the setUp of a unittest.TestCase, so
        we know the signature.
        """
        test.session = requests.Session()
        test.session.auth = (
            test._env.get('TESTY_DB_ADMIN_USER'),
            test._env.get('TESTY_DB_ADMIN_PASS')
        )
        test.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-cloudant-user": test._env.get('TESTY_DB_ADMIN_USER')
        })

        return f(test)
    return decorator


class HttpTestCase(unittest.TestCase):
    @setup_session
    def setUp(self):
        pass

    def get(self, url, params={}, headers={}, do_raise=True):
        r = self.session.get(url, params=params, headers=headers)
        if do_raise:
            r.raise_for_status()
        return r

    def post(self, url, params={}, data={}, headers={}, do_raise=True):
        r = self.session.post(url, params=params, data=data, headers=headers)
        if do_raise:
            r.raise_for_status()
        return r

    def put(self, url, params={}, data={}, headers={}, do_raise=True):
        r = self.session.put(url, params=params, data=data, headers=headers)
        if do_raise:
            r.raise_for_status()
        return r

    def delete(self, url, params={}, data={}, headers={}, do_raise=True):
        r = self.session.delete(url, params=params, data=data, headers=headers)
        if do_raise:
            r.raise_for_status()
        return r

    # Adding these for re-usability
    def create_test_db(self):
            """
            Create the default test database
            """
            return self.session.put(self._env['TESTY_DB_URL'])

    def delete_test_db(self):
            return self.session.delete(self._env['TESTY_DB_URL'])


    def check_bulk_insert(self, resp):
        """
        Using the response from a bulk_docs POST, this function checks
        that all documents were inserted correctly or causes an assertion
        failure.
        """
        assert_that(resp.status_code, is_in([200, 201, 202]),
                    "Bulk docs POST failed (status code {0})".format(resp.status_code))
        assert_that(resp.json(), is_(instance_of(list)),
                    "Bulk docs insert didn't return a list")

        for insert_result in resp.json():
            assert_that(insert_result, is_not(has_key("error")),
                        "Error(s) found in a bulk doc insert response list")
        return resp
