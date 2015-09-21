#!/bin/bash

pushd `dirname $0` > /dev/null

VIRTUALENV=`which virtualenv`
if [[ -z $VIRTUALENV ]]; then
    VIRTUALENV="/usr/local/bin/virtualenv"
fi

if [ ! -d ./venv/ ]; then
    echo -n "Initializing virtualenv..."
    $VIRTUALENV venv
    ./venv/bin/pip install -r requirements.txt
    echo "ok"
fi

echo -n "Starting virtualenv..."
    source venv/bin/activate
    echo "ok"

#TESTY_JENKINS_RUN variable is used by testy (see testy/testy/utils/http) to skip tests that will not run on the jenkins server.  
export TESTY_JENKINS_RUN=true

exec ./runtesty.py --db_admin_user=$1 \
    --db_admin_pass=$2 \
    --db_admin_root=http://$1.cloudant.com \
    --timeout=100 \
    suites/api/test_api.py \
    suites/api/test_attachments.py \
    suites/api/test_design_documents.py \
    suites/api/test_filtered_changes_feeds.py \
    suites/api/test_multipart_status_codes.py \
    suites/api/test_replication.py \
    suites/api/test_search_grouping_api.py \
    suites/api/test_local_documents.py \
    suites/api/test_query.py
