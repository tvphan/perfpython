#!/usr/bin/env python
##################################################################
# Licensed Materials - Property of IBM
# (c) Copyright IBM Corporation 2015. All Rights Reserved.
# 
# Note to U.S. Government Users Restricted Rights:  Use,
# duplication or disclosure restricted by GSA ADP Schedule 
# Contract with IBM Corp.
##################################################################

import baseBenchmarkWorker as bBW
import testy.suites.api.test_lucene_queries as TLQ
import logging
import requests

class benchmark_test_lucene_queries(bBW.baseBenchmarkWorker, TLQ.TestLuceneQueries):
    '''
    classdocs
    '''

    def __init__(self, db, insertedIDs, params=None):
        '''
        Constructor
        '''
        bBW.baseBenchmarkWorker.__init__(self,db)
        
        # Jump table to classes "own" methods indirectly
                
        #TODO: actions (action : actionMethod)  default ratios (action: 1) 
        self.addActions({  #TODO: introspection could probably lookup the name of self.test_ methods and calculate everything
                         "test_result_json_structure" : benchmark_test_lucene_queries.test_result_json_structure,
                         "test_bookmark_has_no_rows" : benchmark_test_lucene_queries.test_bookmark_has_no_rows,
                         "test_bookmark_has_rows" : benchmark_test_lucene_queries.test_bookmark_has_rows,
                         "test_bookmark_invalid" : benchmark_test_lucene_queries.test_bookmark_invalid,
                         "test_stale_ok" : benchmark_test_lucene_queries.test_stale_ok,
                         "test_limit_of_x" : benchmark_test_lucene_queries.test_limit_of_x,
                         "test_include_x_doc" : benchmark_test_lucene_queries.test_include_x_doc,
                         "test_include_doc_false" : benchmark_test_lucene_queries.test_include_doc_false,
                         "test_sort_ascending_number" : benchmark_test_lucene_queries.test_sort_ascending_number,
                         "test_sort_descending_number" : benchmark_test_lucene_queries.test_sort_descending_number,
                         "test_sort_ascending_string" : benchmark_test_lucene_queries.test_sort_ascending_string,
                         "test_sort_descending_string" : benchmark_test_lucene_queries.test_sort_descending_string,
                         "test_group_field_number_is_unsupported" : benchmark_test_lucene_queries.test_group_field_number_is_unsupported,
                         "test_group_field_string" : benchmark_test_lucene_queries.test_group_field_string,
                         "test_group_field_string_with_row_limit" : benchmark_test_lucene_queries.test_group_field_string_with_row_limit,
                         "test_group_field_string_with_group_limit" : benchmark_test_lucene_queries.test_group_field_string_with_group_limit,
                         "test_group_field_string_sort_ascending" : benchmark_test_lucene_queries.test_group_field_string_sort_ascending,
                         "test_group_field_string_sort_descending" : benchmark_test_lucene_queries.test_group_field_string_sort_descending,
                         "test_ranges" : benchmark_test_lucene_queries.test_ranges,
                         "test_counts" : benchmark_test_lucene_queries.test_counts,
                         "test_drilldown" : benchmark_test_lucene_queries.test_drilldown,
                         "test_query" : benchmark_test_lucene_queries.test_query,
                         "test_include_fields" : benchmark_test_lucene_queries.test_include_fields,
                         "test_include_fields_invalid_fields" : benchmark_test_lucene_queries.test_include_fields_invalid_fields,
                         })
        if params is not None:
            self.params = params
            
        if "actionRatios" in params and params["actionRatios"] is not None:
            self.ratios = params["actionRatios"]
        else:
            log = logging.getLogger('mtbenchmark')
            log.warn("params have not been set, using fallback")
            self.addRatios({
                            "test_result_json_structure" : 1,
                            "test_bookmark_has_no_rows" : 1,
                            "test_bookmark_has_rows" : 1,
                            "test_bookmark_invalid" : 1,
                            "test_stale_ok" : 1,
                            "test_limit_of_x" : 1,
                            "test_include_x_doc" : 1,
                            "test_include_doc_false" : 1,
                            "test_sort_ascending_number" : 1,
                            "test_sort_descending_number" : 1,
                            "test_sort_ascending_string" : 1,
                            "test_sort_descending_string" : 1,
                            "test_group_field_number_is_unsupported" : 1,
                            "test_group_field_string" : 1,
                            "test_group_field_string_with_row_limit" : 1,
                            "test_group_field_string_with_group_limit" : 1,
                            "test_group_field_string_sort_ascending" : 1,
                            "test_group_field_string_sort_descending" : 1,
                            "test_query" : 1,
                            "test_include_fields" : 1,
                            "test_include_fields_invalid_fields" : 1,
                            # These are turned off for now
                            "test_ranges" : 0,
                            "test_counts" : 0,
                            "test_drilldown" : 0                            
                  })
            

        # Configure Environment as expected by the testy tests 
        """
        self._env={
            "TESTY_CLOUDANT_CONTEXT":"",
            "TESTY_CLUSTER":"",
            "TESTY_CLUSTER_LB":"",
            "TESTY_CLUSTER_NODENAMES":"",
            "TESTY_CLUSTER_URL":"",
            "TESTY_DB_ADMIN_PASS":"",
            "TESTY_DB_ADMIN_ROOT":"",
            "TESTY_DB_ADMIN_USER":"",
            "TESTY_DB_NAME":"",
            "TESTY_DB_READ_PASS":"",
            "TESTY_DB_READ_USER":"",
            "TESTY_DB_URL":"",
            "TESTY_DB_WRITE_PASS":"",
            "TESTY_DB_WRITE_USER":"",
            "TESTY_NO_CLEAN_TMP":"",
            "TESTY_RESULT_DIR":"",
            "TESTY_SAVE_PASS":"",
            "TESTY_SAVE_URL":"",
            "TESTY_SAVE_USER":"",
            "TESTY_TIMESTART":"",
            "TESTY_TMP_DIR":""
                   }"""
        self._env={
            "TESTY_DB_ADMIN_PASS":params["dbConfig"]["auth"][1],
            "TESTY_DB_ADMIN_USER":params["dbConfig"]["auth"][0],
            "TESTY_DB_URL":params["dbConfig"]["dburl"]+"/"+params["dbConfig"]["dbname"]}
        
        # TODO: perhaps stick in our session from pycloudantDB?
        self.session = requests.Session()
        self.session.auth = (
            self._env.get('TESTY_DB_ADMIN_USER'),
            self._env.get('TESTY_DB_ADMIN_PASS')
        )
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-cloudant-user": self._env.get('TESTY_DB_ADMIN_USER')
        })
        self.tearDown()
        self.setUp()
        
        # Disable checking of the response since the unit tests don't return anything. 
        self.executingUnitTests = True
        
        # Toggle flag to only do non-context aware asserts
        self.perfTesting = True
        
        
        self.SEARCH_URL = "/_design/lookup/_search/all"
        self.viewName = "lookup"
        self.m = {
           "wildcard1":"Registrant.RegistrantName:A*",
           "query1":"Issues.SpecificIssue:Health",
           "query2":"Issues.SpecificIssue:ACCOUNTING",
           "sort_num":"Filing.Amount<number>",
           "sort_num_rev":"-Filing.Amount<number>",
           "sort_str":"Client.ClientPPBState<string>",
           "sort_str_rev":"-Client.ClientPPBState<string>",
           "group_by":"Client.ClientState",
           "group_by_sort":"Client.ClientState<string>",
           "group_by_sort_rev":"-Client.ClientState<string>",
           "include_field":"Filing.Amount",
           "include_invalid_field":"Filing.Amount_FAKE"
           }
        
        
        
    def tearDown(self):
        if self.params["dbConfig"]["cleanupDatabase"]:
            self.delete_test_db()
        
    def setUp(self):
        if self.params["dbConfig"]["freshDatabase"]:
            TLQ.TestLuceneQueries.setUp(self)
        
 