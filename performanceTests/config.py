config={
    "templateFile" : "templates/iron_template.json",
    "concurrentThreads" : 1,
    # Iterations used for the mail operations
    "iterationPerThread" : 400,
    
    # Size and number of bulk inserts
    "bulkInsertSize" : 1000,
    "bulkInsertsPerThread" : 25,
    
    # Ratios to control the proportion of different actions
    "actionRatios" : {
          "simpleInsert" : 1,
          "randomDelete" : 1,
          "randomRead" : 1,
          "randomUpdate" : 1,
          "bulkInsert" : 0 },
    
    # If this is unset, it will generate a timestamped filename
    "resultsFileName" : "TaskData.json",
    
    # Database configuration
    "dbConfig" : {
        # URL to the cloudant instance
        "dburl" : ("https://<dbUrl>"),
    
        # Username & Password 
        "auth" : ('<user>','<passwd>'),
    
        # Database to be used
        "dbname" : "testdb"
   }
}
