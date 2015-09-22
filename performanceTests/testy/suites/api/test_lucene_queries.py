from testy.utils.http import setup_session, HttpTestCase
from testy.utils import test_helpers as helpers
from hamcrest import assert_that, is_, has_length, is_in, has_key, is_not, greater_than
import json
import pytest

SEARCH_URL = '/_design/views101/_search/animals'


class TestLuceneQueries(HttpTestCase):
    @setup_session
    def setUp(self):
        helpers.put_animaldb(self._env['TESTY_DB_URL'],
                             auth=(self._env['TESTY_DB_ADMIN_USER'],
                                   self._env['TESTY_DB_ADMIN_PASS']))

    def tearDown(self):
        if not helpers.skipp_taredown():
            self.delete_test_db()

    def test_result_json_structure(self):
        expected_root_keys = ["total_rows",
                              "bookmark",
                              "rows"]

        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': 'z*'})
        assert_that(response.status_code, is_(helpers.accepted()))

        for key in expected_root_keys:
            assert_that(response.json(), has_key(key))

    def test_bookmark_has_no_rows(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*'})
        assert_that(response.status_code, is_(helpers.accepted()))

        bookmark = response.json()['bookmark']
        bookmark_response = self.session.get(self._env['TESTY_DB_URL'] +
                                             SEARCH_URL,
                                             params={'q': '*:*',
                                                     'bookmark': bookmark})
        assert_that(bookmark_response.status_code, is_(helpers.accepted()))

        assert_that(bookmark_response.json()['rows'], is_([]))

    def test_bookmark_has_rows(self):
        #This test checks if the bookmark fun is working by first limiting
        #the results to 3, and then passing that bookmark to get the
        #remaining 8 rows.
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'limit': 3})
        assert_that(response.status_code, is_(helpers.accepted()))

        bookmark = response.json()['bookmark']
        bookmark_response = self.session.get(self._env['TESTY_DB_URL'] +
                                             SEARCH_URL,
                                             params={'q': '*:*',
                                                     'bookmark': bookmark})
        assert_that(bookmark_response.status_code, is_(helpers.accepted()))
        assert_that(bookmark_response.json()['rows'], has_length(8))

    def test_bookmark_invalid(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'limit': 3})
        assert_that(response.status_code, is_(helpers.accepted()))

        invalid_bookmark = response.json()['bookmark']

        invalid_bookmark = invalid_bookmark.replace("A", "x")

        bookmark_response = self.session.get(self._env['TESTY_DB_URL'] +
                                             SEARCH_URL,
                                             params={'q': '*:*',
                                                     'bookmark': invalid_bookmark})
        assert_that(bookmark_response.json()['reason'],
                    is_('Invalid bookmark parameter supplied'))

    def test_stale_ok(self):
        #We will need to develop tests that assess that stale: ok
        #dose what it says on the tin
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': 'kookaburra',
                                            'stale': 'ok'})
        assert_that(response.status_code, is_(helpers.accepted()))

    def test_limit_of_x(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'limit': 4})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'], has_length(4))

    def test_include_x_doc(self):
        #In this test I check for the exsistance of the "wiki_page" field as
        #it is not stored by the search index. (implicently checking the 'doc'
        #field also.)
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': 'zebra',
                                            'include_docs': 'true'})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][0]['doc'], has_key('wiki_page'))

    def test_include_doc_false(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': 'zebra',
                                            'include_docs': 'false'})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][0], is_not(has_key('docs')))

    def test_sort_ascending_number(self):
        #In this test I check that the first doc returned (oddly, after the DDoc?)
        #is the snipe as it is the smallest animal in ADB
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'sort': json.dumps(["min_length<number>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][1]['id'], is_('snipe'))

    def test_sort_descending_number(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'sort': json.dumps(["-min_length<number>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][1]['id'], is_('elephant'))

    def test_sort_ascending_string(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'sort': json.dumps(["latin_name<string>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][10]['id'], is_('aardvark'))

    def test_sort_descending_string(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'sort': json.dumps(["-latin_name<string>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['rows'][0]['id'], is_('aardvark'))

    def test_group_field_number_is_unsupported(self):
        reason = u'Group by number not supported. Group by string terms only.'
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'group_field': 'min_length<number>'})

        assert_that(response.status_code, is_(helpers.bad_request()),
                    "Grouping by number is disallowed in cloudant")
        assert_that(response.json()['reason'], is_(reason))

    def test_group_field_string(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'group_field': 'diet'})

        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['groups'], has_length(4))

    def test_group_field_string_with_row_limit(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'limit': 2,
                                            'group_field': 'diet'})
        assert_that(response.status_code, is_(helpers.accepted()))
        for group in response.json()['groups']:
            assert_that(group['rows'], greater_than(2),
                        'There is a group with more that 2 rows.')

    def test_group_field_string_with_group_limit(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'group_limit': 2,
                                            'group_field': 'diet'})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['groups'], has_length(2))

    def test_group_field_string_sort_ascending(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'group_field': 'diet',
                                            'group_sort': json.dumps(["diet<string>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['groups'][1]['by'], is_('carnivore'))

    def test_group_field_string_sort_descending(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'q': '*:*',
                                            'group_field': 'diet',
                                            'group_sort': json.dumps(["-diet<string>"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['groups'][0]['by'], is_('omnivore'))

    @pytest.mark.timeout(40)
    def test_ranges(self):
        #For this test we need to add a new search index to ADB, one that
        #supportes search faciting.
        new_index = """function(doc){\n if (doc.min_length) {\n
                       index(\"length\", parseInt(doc.min_length, 10),
                       {\"facet\":true});\n }\n}
                    """
        index = {"analyzer": "standard",
                 "index": new_index}
        self.update_ddoc('length_range', index)

        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL.replace("animals", "length_range"),
                                    params={'q': '*:*',
                                            'ranges': json.dumps({"length":
                                                                  {"small": "[0 TO 1]",
                                                                   "big": "[2 TO 5]"}})})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['ranges']['length']['big'], is_(3.0))
        assert_that(response.json()['ranges']['length']['small'], is_(7.0))

    @pytest.mark.timeout(40)
    def test_counts(self):
        #For this test we need to add a new search index to ADB, one that
        #supportes search faciting.
        new_index = """function(doc){\n if(doc.min_length){\n
                       index(\"min_length\", doc.min_length, {\"store\":
                       \"yes\", \"facet\": true});\n  }\n  if (doc['class'])
                       {\n    index(\"class\", doc['class'], {\"store\": 
                       \"yes\",\"facet\": true});\n }\n}
                    """
        index = {"analyzer": "standard",
                 "index": new_index}
        self.update_ddoc('class_count', index)

        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL.replace("animals", "class_count"),
                                    params={'q': 'min_length:[0 TO 20]',
                                            'counts': json.dumps(["class"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['counts']['class']['bird'], is_(2.0))
        assert_that(response.json()['counts']['class']['mammal'], is_(8.0))

    def test_drilldown(self):
        new_index = """function(doc){\n if(doc.min_length){\n
                       index(\"min_length\", doc.min_length,
                       {\"store\": \"yes\", \"facet\": true});\n  }\n  if
                       (doc['class']){\n    index(\"class\", doc['class'],
                       {\"store\": \"yes\", \"facet\": true});\n }\n}
                    """
        index = {"analyzer": "standard",
                 "index": new_index}
        self.update_ddoc('class_count', index)

        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL.replace("animals", "class_count"),
                                    params={'q': 'min_length:[0 TO 2]',
                                            'drilldown': json.dumps(["class", "mammal"])})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['total_rows'], is_(6))

    def test_query(self):
        response = self.session.get(self._env['TESTY_DB_URL'] +
                                    SEARCH_URL,
                                    params={'query': '*:*'})
        assert_that(response.status_code, is_(helpers.accepted()))
        assert_that(response.json()['total_rows'],
                    is_(11))

    def test_include_fields(self):
        response = self.get_include_fields_wildcard_q('min_length')

        assert_that(response.status_code, is_(helpers.accepted()))

        for row in response.json()['rows']:
            if row['id'] == "_design/views101":
                pass
            else:
                assert_that(row['fields'].keys(), is_([u'min_length']))

    def test_include_fields_invalid_fields(self):
        response = self.get_include_fields_wildcard_q('wiki_page')

        assert_that(response.status_code, is_(helpers.accepted()))

        for row in response.json()['rows']:
            if row['id'] == "_design/views101":
                pass
            else:
                assert_that(row['fields'].keys(), is_([]))

    #
    # Test helper functions
    #

    def delete_test_db(self):
        return self.session.delete(self._env['TESTY_DB_URL'])

    def update_ddoc(self, index_name, index):
        ddoc = self.session.get(self._env['TESTY_DB_URL'] +
                                '/_design/views101')

        ddoc_data = ddoc.json()
        ddoc_data['indexes'][index_name] = index

        response = self.session.put(self._env['TESTY_DB_URL'] +
                                    '/_design/views101',
                                    params={'_rev': ddoc_data['_rev']},
                                    data=json.dumps(ddoc_data))
        assert_that(response.status_code, is_(helpers.accepted()))

        return response

    def get_include_fields_wildcard_q(self, field):
        return self.session.get(self._env['TESTY_DB_URL'] +
                                SEARCH_URL,
                                params={'query': '*:*',
                                        'include_fields': json.dumps([field])})
