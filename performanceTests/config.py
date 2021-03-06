config={
    "globalConfig":{
        "templateFile" : "templates/iron_template.json",
        "concurrentThreads" : 1,
        # Iterations used for the mail operations
        "iterationPerThread" : 4000,
        
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
        
        # Database configuration
        "dbConfig" : {
            # URL to the cloudant instance
            "dburl" : ("https://<dbUrl>"),
        
            # Username & Password 
            "auth" : ('<user>','<passwd>'),
        
            # Database to be used
            "dbname" : "testdb",
            
            #   If True it will create database <dbname>
            #   If False it will reuse database <dbname>
            "freshDatabase" : True,
            
            # Delete Database after run?
            "cleanupDatabase" : True,

        }
                    
    },
    
    # Stages to execute:
    # Default Stages
    "workerStages" : [{"threadWorker_simple_datapop":{
                                # Worker function to be called
                                "stageFunction" : "threadWorker_simple_datapop",
                                
                                # Control the size of the database, 250 x 1000 docs
                                "iterationPerThread" : 250,
                                "bulkInsertSize" : 1000,
                                
                                # Ratios to control the proportion of different actions
                                "actionRatios" : {
                                      "simpleInsert" : 0,
                                      "randomDelete" : 0,
                                      "randomRead" : 0,
                                      "randomUpdate" : 0,
                                      "bulkInsert" : 1 },
                                                
                                 }}, 
                      
                      {"threadWorker_CRUD":{
                                # Worker function to be called
                                "stageFunction":"threadWorker_CRUD"
                                }}, 
                      
                      {"threadWorker_CRUD_SkipLB":{
                                # Worker function to be called
                                "stageFunction":"threadWorker_CRUD_SkipLB",
                                
                                # Ratios to control the proportion of different actions
                                "actionRatios" : {
                                      "noLB_simpleInsert" : 1,
                                      "noLB_randomDelete" : 1,
                                      "noLB_randomRead" : 1,
                                      "noLB_randomUpdate" : 1,
                                      "noLB_bulkInsert" : 0
                                },
                                
                                # Database configuration for hitting one of the DB nodes directly
                                "dbConfig" : {     
                                    # URL to the cloudant instance
                                    "dburl" : ("https://<dbUrl>"),                               
                                    
                                    # Extra headers to pretend to be the LB
                                    "extraHeaders" : {"X-Cloudant-User":"<user>"}
                                }
                                }},
                      # To enable the testy lucene tests, uncomment this block
                      #"threadWorker_testy_lucene":{
                      #          # Worker function to be called
                      #          "stageFunction" : "threadWorker_testy_lucene",
                      #          
                      #          # Ratios to control the proportion of different actions
                      #          "actionRatios" : None,
                      #           }},
                      ], # end of worker stages

}
