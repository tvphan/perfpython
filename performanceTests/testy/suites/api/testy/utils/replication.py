"""
Util functions for replication unit tests
"""
from collections import defaultdict
import json
import requests
import time
from time import mktime
import os.path
import httplib


def clearUp(replications, group_id, root, authen):
    # remove the _replicator and all the test dbs that were made
    for i in xrange(replications):
        destination = root + '/test-%s-%s-%s' % (group_id, replications, i)
        requests.delete(destination, auth=authen)


def chunks(l, n):
    return [l[i:i+n] for i in xrange(0, len(l), n)]


def bulk(url, docs, authen):
    requests.post(
        '%s/_bulk_docs' % url,
        data=json.dumps(docs),
        headers={'content-type': 'application/json'},
        auth=authen
    )


def save(results_dir, results):
    path = os.path.join(
        results_dir,
        'results.json'
    )
    with open(path, 'w') as json_file:
        json.dump(results, json_file)

    print results


def make_replications(group_id, root, env, authen, **kwargs):
    # optional inputs: delay, replications, continuous, bulksize
    replications = kwargs.get('replications', 0)
    bulk_docs = {'docs': []}

    url = os.path.join(
        root,
        '_replicator'
    )
    requests.put(url, auth=authen)

    env.append(root[8:])

    ids = []
    source = 'https://%s:%s@%s' % (env[0], env[1], env[2])

    for i in xrange(replications):
        time.sleep(kwargs.get('delay', 0))
        destination = os.path.join(
            'https://%s:%s@%s' % (env[0], env[1], env[3]),
            'test-%s-%s-%s' % (group_id, replications, i)
        )
        requests.delete(destination, auth=authen)
        repl = {
            '_id': '%s-%s-%s' % (group_id, replications, i),
            'source': source,
            'target': destination,
            'create_target': True,
            "timestamp": "%s" % time.time()
        }
        if kwargs.get('continuous', False):
            repl["continuous"] = True
        bulk_docs['docs'].append(repl)
        if len(bulk_docs['docs']) > kwargs.get('bulksize', 1000):
            bulk(url, bulk_docs, authen)
            ids.extend([x['_id'] for x in bulk_docs['docs']])
            bulk_docs['docs'] = []

    bulk(url, bulk_docs, authen)
    ids.extend([x['_id'] for x in bulk_docs['docs']])

    return ids


def __parse(**kwargs):
    repl = kwargs.get('repl')
    authen = kwargs.get('authen')
    bytes_to_mega = 1048576.0

    finish = time.strptime(
        repl['doc'].get('_replication_state_time', False),
        "%Y-%m-%dT%H:%M:%S+00:00"
    )
    duration = mktime(finish) - float(repl['doc']['timestamp'])
    doc_location = kwargs.get('root')+'/_replicator/'+repl['id']
    doc = requests.get(doc_location, auth=authen)
    rev = {'rev': doc.headers['etag'][1:-1]}
    requests.delete(doc_location, params=rev, auth=authen)
    db = requests.get(repl['doc'].get('target', False))
    disk = db.json()['disk_size']/(duration*bytes_to_mega)
    data = db.json()['other']['data_size']/(duration*bytes_to_mega)
    doc_rate = (kwargs.get('docs', 1000))/duration

    return (duration, disk, data, doc_rate)


def __check_and_update_record(**kwargs):
    repl = kwargs.get('repl')
    record = kwargs.get('record')
    ids = kwargs.get('ids')
    state = repl['doc'].get('_replication_state', False)
    # remove completed replications
    if (state in ['completed', 'error']) or (kwargs.get('continuous', False)):
        ids.remove(repl['id'])
        record['counts'][state] += 1
        parsed = __parse(**kwargs)
        duration = parsed[0]
        record['duration'][state] += duration
        record['disk'].append(parsed[1])
        record['data'].append(parsed[2])
        record['doc_rate'].append(parsed[3])
        if (record['min_time'] > duration) or (record['min_time'] < 0):
            record['min_time'] = duration
        if record['max_time'] < duration:
            record['max_time'] = duration
    # update record with (c, dur, min_time, max_time, disk, data, doc_rate)
    return record, ids


def monitor_replications(root, authen, ids, **kwargs):
    # optional inputs: docs, continuous
    """
    wait till all replications are done
    once a replication is finished delete from _replicator
    record min, max time, number in each state, total duration
    also record mb/s of each replication (disk and data)
    """
    record = dict(
        counts=defaultdict(int),
        duration=defaultdict(int),
        min_time=-1,
        max_time=-1,
        disk=[],
        data=[],
        doc_rate=[]
    )
    while len(ids) > 0:
        if kwargs.get('continuous', False):
            time.sleep(300)
        else:
            time.sleep(5)
        # hit active tasks
        url = os.path.join(
            root,
            '_replicator/_all_docs'
        )
        for chunk in chunks(ids, 100):
            d = requests.post(
                url,
                params={'include_docs': 'true'},
                data=json.dumps({'keys': chunk}),
                headers={'content-type': 'application/json'},
                auth=authen
            ).json()
            for repl in d['rows']:
                record, ids = __check_and_update_record(
                    repl=repl,
                    record=record,
                    ids=ids,
                    root=root,
                    authen=authen,
                    **kwargs
                )
    return record


def replication_stats(group_id, root, authen, ids, **kwargs):
    # optional inputs: replications, docs, continuous, delay
    try:
        stats = monitor_replications(root, authen, ids, **kwargs)
    except httplib.IncompleteRead, e:
        clearUp(group_id, root, authen, kwargs.get('replications', 100))
        raise httplib.IncompleteRead(e)

    error_ratio = stats['counts']['error'] / sum(stats['counts'].values())
    replications = kwargs.get('replications', 100)

    if kwargs.get('continuous', False):
        curr_results = {
            'error-percent': error_ratio*100,
            'replications': replications,
            'continuous': True
        }
    else:
        curr_results = {
            'error-percent': error_ratio*100,
            'avg-time': sum(stats['duration'].values()) / replications,
            'replications': replications,
            'min-time': stats['min_time'],
            'max-time': stats['max_time'],
            'dest-disk-rates': stats['disk'],
            'dest-data-rates': stats['data'],
            'doc-rate': stats['doc_rate'],
            'continuous': False
        }

    delay = kwargs.get('delay', 0)
    if (delay > 0):
        result = {'%f' % delay: curr_results}
        return result
    return curr_results
