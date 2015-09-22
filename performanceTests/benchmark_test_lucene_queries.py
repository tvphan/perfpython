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
        
        if params is not None and "IGNOREactionRatios" in params:
            self.ratios = params["actionRatios"]
            self.params = params
        else:
            log = logging.getLogger('mtbenchmark')
            log.error("params have not been set, using fallback")
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
                            "test_ranges" : 1,
                            "test_counts" : 1,
                            "test_drilldown" : 1,
                            "test_query" : 1,
                            "test_include_fields" : 1,
                            "test_include_fields_invalid_fields" : 1,
                  })

        # Do one time call to tearDown, setUp to prepare 
        #self.tearDown()
        #self.setUp()
        
 