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

from botocore.stub import Stubber
from verification_rules.check_root_account_mfa.check_root_account_mfa import get_evaluation_elements

#################################################################################
# Fixtures
#################################################################################
@pytest.fixture(scope="function")
def _resp_account_summary_valid():
    return {
        "SummaryMap": {
            "AccountMFAEnabled": 1
        }
    }

@pytest.fixture(scope="function")
def _resp_account_summary_invalid():
    return {
        "SummaryMap": {
            "AccountMFAEnabled": 0
        }
    }

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

@pytest.fixture(scope="function")
def _invoke_event():
    return {"awsAccountId":"123456789012", "notificationCreationTime":"2017-07-11T01:00:41.279Z", "messageType":"ScheduledNotification", "recordVersion":"1.0"}


#################################################################################
# Test Classes
#################################################################################
class TestCheckRootAccountMfa(object):

    def test_compliance_type_root_mfa_enabled(self, _resp_account_summary_valid, _invoke_event):
        boto_iam = boto3.client("iam")
        stubber = Stubber(boto_iam)
        stubber.add_response("get_account_summary", _resp_account_summary_valid)

        stubber.activate()
        evaluation_elements = get_evaluation_elements(boto_iam, _invoke_event)
        stubber.deactivate()
        assert evaluation_elements
        assert evaluation_elements[0].compliance_type == 'COMPLIANT'
        assert evaluation_elements[0].resource_type == 'AWS::::Account'
        assert evaluation_elements[0].resource_id == '123456789012'
        assert evaluation_elements[0].ordering_timestamp == '2017-07-11T01:00:41.279Z'
        assert evaluation_elements[0].annotation == 'MFA is enabled for Root account'

    def test_compliance_type_root_mfa_disabled(self, _resp_account_summary_invalid, _invoke_event):
        boto_iam = boto3.client("iam")
        stubber = Stubber(boto_iam)
        stubber.add_response("get_account_summary", _resp_account_summary_invalid)

        stubber.activate()
        evaluation_elements = get_evaluation_elements(boto_iam, _invoke_event)
        stubber.deactivate()
        assert evaluation_elements
        assert evaluation_elements[0].compliance_type == 'NON_COMPLIANT'
        assert evaluation_elements[0].resource_type == 'AWS::::Account'
        assert evaluation_elements[0].resource_id == '123456789012'
        assert evaluation_elements[0].ordering_timestamp == '2017-07-11T01:00:41.279Z'
        assert evaluation_elements[0].annotation == 'MFA is Not enabled for Root account'
