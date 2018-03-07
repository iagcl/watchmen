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
import boto3
import pytest
from mock import patch

import python_lib.populate_citizen_account as populate_citizen_account

@pytest.fixture(scope="function")
def _citizen_items_valid():
    return {
        "Items": [
            {
                "AccountId": {"S": "1"},
                "ExecutionRoleArn": {"S": "arn:etc"}
            }
        ]
    }

@patch("boto3.client")
def test_get_table_items(mock_b3_client, _citizen_items_valid):
    mock_b3_client("dynamodb").get_paginator("scan").paginate.return_value = [_citizen_items_valid]

    assert populate_citizen_account.get_table_items(boto3.client("dynamobd"), "TestTable")

@patch("boto3.client")
def test_delete_all_items(mock_b3_client, _citizen_items_valid):
    mock_b3_client("dynamodb").get_paginator("scan").paginate.return_value = \
        [_citizen_items_valid]

    assert populate_citizen_account.delete_all_items(boto3.client("dynamodb"), None) is None

@patch("boto3.client")
def test_main(mock_b3_client):
    assert populate_citizen_account.main() is None
