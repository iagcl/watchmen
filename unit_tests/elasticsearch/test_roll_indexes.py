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

import sys

from collections import OrderedDict

# if not 'watchmen_core' in sys.path:
#     sys.path.append('watchmen_core')

from elasticsearch.roll_indexes.roll_indexes import sort_indices_by_creation_date

_indices = {
        'cwl-1505669279': {
            'aliases': {},
            'mappings': {
                'test_type': {
                    'properties': {
                        'age': {'type': 'long'},
                        'last_updated': {'type': 'long'},
                        'name': {'fields': {'keyword': {'ignore_above': 256, 'type': 'keyword'}},'type': 'text'}
                    }
                }
            },
            'settings': {
                'index': {
                    'provided_name': 'cwl-1505669279',
                    'number_of_replicas': '0',
                    'uuid': '0EaGotYyRqOLpjqVlBVfGg',
                    'number_of_shards': '2',
                    'creation_date': '1505669280205',
                    'version': {'created': '5030299'}
                }
            }
        },
        'cwl-1505651380': {
            'aliases': {},
            'mappings': {
                'test_type': {
                    'properties': {
                        'age': {'type': 'long'},
                        'last_updated': {'type': 'long'},
                        'name': {'fields': {'keyword': {'ignore_above': 256, 'type': 'keyword'}}, 'type': 'text'}
                    }
                }
            },
            'settings': {
                'index': {
                    'provided_name': 'cwl-1505651380',
                    'number_of_replicas': '0',
                    'uuid': 'wb2kAALwQ6amD6PkV7__xQ',
                    'number_of_shards': '2',
                    'creation_date': '1505651380891',
                    'version': {'created': '5030299'}
                }
            }
        },
        'cwl-1505647797': {
            'aliases': {},
            'mappings': {
                'test_type': {
                    'properties': {
                        'age': {'type': 'long'},
                        'last_updated': {'type': 'long'},
                        'name': {'fields': {'keyword': {'ignore_above': 256, 'type': 'keyword'}}, 'type': 'text'}
                    }
                }
            },
            'settings': {
                'index': {
                    'provided_name': 'cwl-1505647797',
                    'number_of_replicas': '0',
                    'uuid': 'Aj9DzCQWRUKVmDH1A8-k-w',
                    'number_of_shards': '2',
                    'creation_date': '1505647797635',
                    'version': {'created': '5030299'}
                }
            }
        }
    }

class TestRollIndexes(object):

    def test_sort_indices_by_creation_date(self):
        es_indices = _indices
        sorted_indices = sort_indices_by_creation_date(es_indices)
        assert sorted_indices == OrderedDict([
            ('cwl-1505669279', '1505669280205'),
            ('cwl-1505651380', '1505651380891'),
            ('cwl-1505647797', '1505647797635')
        ])
