config={
    "templateFile" : "templates/iron_template.json",
    "concurrentThreads" : 10,
    "iterationPerThread" : 100,
    "bulkInsertSize" : 10,
    "actionRatios" : {
          "simpleInsert" : 50,
          "randomDelete" : 25,
          "randomRead" : 25,
          "randomUpdate" : 25,
          "bulkInsert" : 5
            },                   
    "dbConfig" : {
        # URL to the cloudant instance
        "dburl" : ("https://<dbUrl>"),
    
        # Username & Password 
        "auth" : ('username','password'),
    
        # Database to be used
        "dbname" : "testdb"
   }

}