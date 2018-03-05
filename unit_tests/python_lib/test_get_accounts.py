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
from botocore.stub import Stubber

import python_lib.get_accounts as get_accounts

@pytest.fixture(scope="function")
def _resp_assume_role_valid():
    return {
        "AssumedRoleUser": {
            "AssumedRoleId": "AROAI4WM4ITKVYXUVZ7VQ:RoleId",
            "Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/RoleId"
        },
        "Credentials": {
            "SecretAccessKey": "secretAccessKey",
            "SessionToken": "sessionToken",
            "Expiration": "2017-06-02T03:22:31Z",
            "AccessKeyId": "accessKeyId12345"
        }
    }

def test_get_assumed_creds_arn_valid(_resp_assume_role_valid):
    sts = boto3.client("sts")

    stubber = Stubber(sts)
    stubber.add_response("assume_role", _resp_assume_role_valid)

    stubber.activate()

    assumed_creds = get_accounts.get_assumed_creds(
        sts,
        "arn:aws:iam::123456789012:role/aws-config-role"
    )

    stubber.deactivate()

    assert assumed_creds.get("aws_access_key_id") == "accessKeyId12345"
    assert assumed_creds.get("aws_secret_access_key") == "secretAccessKey"
    assert assumed_creds.get("aws_session_token") == "sessionToken"

def test_assumed_creds_arn_blank():
    assert get_accounts.get_assumed_creds(None, "") == {}

def test_get_csv_accounts():
    assert get_accounts.get_csv_accounts()

@patch("boto3.client")
def test_get_accounts(mock_b3_client):
    assert get_accounts.get_accounts()
