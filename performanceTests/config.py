config={
    "templateFile" : "templates/iron_template.json",
    "concurrentThreads" : 1,
    # Iterations used for the mail operations
    "iterationPerThread" : 4000,
    
    # Size and number of bulk inserts
    "bulkInsertSize" : 1000,
    "bulkInsertsPerThread" : 250,
    
    # Limiting the number of Requests per second, (-1 for unlimited)
    "maxReqPerSec" : -1,
    
    # Ratios to control the proportion of different actions
    "actionRatios" : {
          "simpleInsert" : 1,
          "randomDelete" : 1,
          "randomRead" : 1,
          "randomUpdate" : 1,
          "bulkInsert" : 0 },
    
    # If this is unset, it will generate a timestamped filename
    "resultsFileName" : "TaskData.json",
    
    # Stages to execute:
    # Default Stages
    "workerStages" : ["threadWorker_preStage", "threadWorker_mainStage", "threadWorker_mainStage_SkipLB"],
    # Lucene Search Stage
    #"workerStages": ["threadWorker_mainStage_lucene_queries"],
        
    # Database configuration
    "dbConfig" : {
        # URL to the cloudant instance
        "dburl" : ("https://<dbUrl>"),
    
        # Username & Password 
        "auth" : ('<user>','<passwd>'),
    
        # Database to be used
        "dbname" : "testdb"
    },
    
    # The number of iterations when hitting one of the DB nodes directly
    "noLbIterationsPerThread" : 1000,
    
    # Database configuration for hitting one of the DB nodes directly
    "noLbDbConfig" : {
        # URL to the cloudant instance
        "dburl" : ("http://<dbUrl>"),
    
        # Username & Password 
        "auth" : ('<user>','<passwd>'),
    
        # Database to be used
        "dbname" : "testdb",
        
        # Extra headers to pretend to be the LB
        "extraHeaders" : {"X-Cloudant-User":"<user>"}
    }


}
