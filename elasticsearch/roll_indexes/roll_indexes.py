# Copyright 2017 Insurance Australia Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
'''
connect to the provided elasticsearch cluster,
check if the available storage space is below a given threshold
if so fetch the indexes that begin with the provided prefix,
remove the oldest index, and repeat until enough space is free
'''

import os
import json
from collections import OrderedDict
import sys ; sys.path.append('./packages/')
from packages.elasticsearch import Elasticsearch, RequestsHttpConnection
from packages.aws_requests_auth.aws_auth import AWSRequestsAuth

def log_event(event, context, message):
    '''log events as json'''
    log = event.copy()

    if context:
        log["requestId"] = context.aws_request_id
        log["memoryLimit"] = context.memory_limit_in_mb
        log["remainingTime"] = context.get_remaining_time_in_millis()
        log["functionArn"] = context.invoked_function_arn
        log["functionName"] = context.function_name
        log["functionVersion"] = context.function_version

    if message:
        log["message"] = message

    print json.dumps(log)

def get_aws_auth(elasticsearch_host):
    '''
        returns an authorisation token for a given elasticsearch host
    '''

    aws_region = os.environ['AWS_REGION'] if "AWS_REGION" in os.environ else 'ap-southeast-2'

    auth = AWSRequestsAuth(
        aws_access_key=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        aws_token=os.environ['AWS_SESSION_TOKEN'],
        aws_host=elasticsearch_host,
        aws_region=aws_region,
        aws_service='es'
    )
    return auth

def get_es_client(elasticsearch_host, auth):
    '''
        returns an elasticsearch client for a given elasticsearch host
    '''
    es_client = Elasticsearch(
        host=elasticsearch_host,
        port=443,
        use_ssl=True,
        verify_ssl=True,
        connection_class=RequestsHttpConnection,
        http_auth=auth,
        timeout=60
    )
    return es_client

def get_indices(es_client, index_prefix):
    '''
        returns the indices that match a prefix
    '''
    es_indices = json.loads(json.dumps(es_client.indices.get(index=index_prefix)))
    return es_indices

def sort_indices_by_creation_date(es_indices):
    '''
        returns an ordered dictionary of index names
        ordered by their creation date with the oldest first
    '''
    es_name_creation = dict()

    # put the index name and creation date into a dictionary
    for es_index in es_indices:
        idx_creation_date = es_indices[es_index]['settings']['index']['creation_date']
        idx_provided_name = es_indices[es_index]['settings']['index']['provided_name']
        es_name_creation[idx_provided_name] = idx_creation_date

    # convert the dictionary into an ordered dictionary (by creation date)
    es_sorted_indices = OrderedDict(
        sorted(
            es_name_creation.iteritems(),
            key=lambda (k, v): (v, k),
            reverse=True
        )
    )

    return es_sorted_indices

def delete_es_index(es_client, es_index):
    '''
        deletes the provided index from the elasticsearch client
    '''
    deleted_index = es_client.indices.delete(index=es_index)
    return deleted_index

def cat_es_index(es_client, es_index):
    '''
        return information about the index as json
    '''
    index_info = es_client.cat.indices(index=es_index, format='json', bytes='b')
    return index_info.pop()

def get_filesystem_stats(es_client):
    '''
        returns stats about the clusters filesystem
    '''
    stats = es_client.cluster.stats()
    return stats['nodes']['fs']

def lambda_handler(event, context):
    '''
        connect to an elasticsearch host and delete the oldest index
        ideally triggered from a low disk space cloudwatch alarm
    '''
    log_event(event, context, None)

    # fetch the environment variables
    if "elasticsearch_host" in os.environ:
        elasticsearch_host = os.environ['elasticsearch_host']
    else:
        elasticsearch_host = None

    index_prefix = os.environ['index_prefix'] if "index_prefix" in os.environ else None
    min_free_bytes = os.environ['min_free_bytes'] if "min_free_bytes" in os.environ else None

    log_event(event, None, json.dumps({
        'environment_variables': {
            'elasticsearch_host': elasticsearch_host,
            'index_prefix': index_prefix,
            'min_free_bytes': min_free_bytes
        }
    }))

    # only run if we have all the environment variables
    if elasticsearch_host and index_prefix and min_free_bytes:
        auth = get_aws_auth(elasticsearch_host)
        es_client = get_es_client(elasticsearch_host, auth)

        es_filesystem_stats = get_filesystem_stats(es_client)
        es_total_in_bytes = es_filesystem_stats['total_in_bytes']
        es_avail_in_bytes = es_filesystem_stats['available_in_bytes']

        # AWS reserves some space for internal operations (19.2%)
        # subtract this from what elasticsearch says it has
        aws_reserved_bytes = int(es_total_in_bytes) * 0.192
        aws_avail_in_bytes = int(es_avail_in_bytes) - int(aws_reserved_bytes)

        # if the available space is less than what we want free
        if int(aws_avail_in_bytes) < int(min_free_bytes):
            delete_list = set()
            delete_size = 0
            new_free = 0

            # get the indexes and sort them by creation date
            es_indices = get_indices(es_client, index_prefix)
            es_sorted_indices = sort_indices_by_creation_date(es_indices)

            # loop through the indices from the oldest first and add them to a list
            # when we have enough that deleting them will put us back over our
            # minimum free space then stop
            while int(new_free) < int(min_free_bytes):
                oldest_index = es_sorted_indices.popitem(last=True)[0]
                index_size = cat_es_index(es_client, oldest_index)['store.size']

                delete_list.add(oldest_index)
                delete_size = int(delete_size) + int(index_size)
                new_free = int(aws_avail_in_bytes) + int(delete_size)

            # print the details so we know what will (or has) happened
            log_event(event, None, json.dumps({
                'es_total_in_bytes': es_total_in_bytes,
                'es_avail_in_bytes': es_avail_in_bytes,
                'aws_reserved_bytes': aws_reserved_bytes,
                'aws_available_bytes': aws_avail_in_bytes,
                'to_delete': str(delete_list),
                'delete_size': delete_size,
                'new_free': new_free
            }))

            # loop through the list and delete the indices
            for index in delete_list:
                log_event(event, None, json.dumps({
                    'index': index,
                    'delete_acknowledged': delete_es_index(es_client, index)['acknowledged']
                }))

        # we are above our minimum free space, nothing to do.
        else:
            log_event(event, None, json.dumps({'aws_avail_in_bytes': aws_avail_in_bytes}))

    else:
        log_event(event, None, json.dumps({'error': 'missing_environment_variables'}))
