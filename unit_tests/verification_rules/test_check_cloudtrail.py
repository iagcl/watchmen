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
from verification_rules.check_cloudtrail.cloudtrail import CloudTrail
from verification_rules.check_cloudtrail.check_cloudtrail import get_compliance_type

#################################################################################
# Fixtures
#################################################################################
@pytest.fixture(scope="function")
def _resp_trails_valid():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": True,
                "IsMultiRegionTrail": True,
                "HasCustomEventSelectors": False,
                "S3BucketName": "mock-cloudtrail-logs",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_invalid():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": True,
                "IsMultiRegionTrail": False,
                "HasCustomEventSelectors": False,
                "S3BucketName": "mock-cloudtrail-logs",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_empty():
    return {
        "trailList": [
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_multi_region_false():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": True,
                "IsMultiRegionTrail": False,
                "HasCustomEventSelectors": False,
                "S3BucketName": "mock-cloudtrail-logs",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_s3_bucket_blank():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": True,
                "IsMultiRegionTrail": True,
                "HasCustomEventSelectors": False,
                "S3BucketName": "",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_encrypt_log_files_true():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": True,
                "IsMultiRegionTrail": True,
                "HasCustomEventSelectors": False,
                "S3BucketName": "mock-cloudtrail-logs",
                "KmsKeyId": "arn:aws:kms:ap-southeast-2:123456789012:key/0c2db3a3-4de6-4a9c-b16f-43bf8c72c27b",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trails_log_file_validation_enabled_false():
    return {
        "trailList": [
            {
                "IncludeGlobalServiceEvents": True,
                "Name": "LumberjackCloudTrail",
                "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail",
                "LogFileValidationEnabled": False,
                "IsMultiRegionTrail": True,
                "HasCustomEventSelectors": False,
                "S3BucketName": "mock-cloudtrail-logs",
                "HomeRegion": "ap-southeast-2"
            }
        ]
    }

@pytest.fixture(scope="function")
def _resp_trail_status_valid():
    return {
        "LatestNotificationTime": 1495417267.116,
        "LatestNotificationAttemptSucceeded": "2017-05-22T01:41:07Z",
        "LatestDeliveryAttemptTime": "2017-05-22T01:41:07Z",
        "LatestDeliveryTime": 1495417267.116,
        "LatestDeliveryAttemptSucceeded": "2017-05-22T01:41:07Z",
        "IsLogging": True,
        "TimeLoggingStarted": "2017-05-15T06:46:43Z",
        "StartLoggingTime": 1494830803.945,
        "LatestDigestDeliveryTime": 1495091093.15,
        "StopLoggingTime": 1494830748.014,
        "LatestNotificationAttemptTime": "2017-05-22T01:41:07Z",
        "TimeLoggingStopped": "2017-05-15T06:45:48Z"
    }

@pytest.fixture(scope="function")
def _resp_trail_status_logging_false():
    return {
        "LatestNotificationTime": 1495417267.116,
        "LatestNotificationAttemptSucceeded": "2017-05-22T01:41:07Z",
        "LatestDeliveryAttemptTime": "2017-05-22T01:41:07Z",
        "LatestDeliveryTime": 1495417267.116,
        "LatestDeliveryAttemptSucceeded": "2017-05-22T01:41:07Z",
        "IsLogging": False,
        "TimeLoggingStarted": "2017-05-15T06:46:43Z",
        "StartLoggingTime": 1494830803.945,
        "LatestDigestDeliveryTime": 1495091093.15,
        "StopLoggingTime": 1494830748.014,
        "LatestNotificationAttemptTime": "2017-05-22T01:41:07Z",
        "TimeLoggingStopped": "2017-05-15T06:45:48Z"
    }

@pytest.fixture(scope="function")
def _resp_event_selectors_valid():
    return {
        "EventSelectors": [
            {
                "IncludeManagementEvents":True,
                "DataResources": [],
                "ReadWriteType": "All"
            }
        ],
        "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail"
    }

@pytest.fixture(scope="function")
def _resp_event_selectors_readwrite_type_read():
    return {
        "EventSelectors": [
            {
                "IncludeManagementEvents":True,
                "DataResources": [],
                "ReadWriteType": "Read"
            }
        ],
        "TrailARN": "arn:aws:cloudtrail:ap-southeast-2:123456789012:trail/mock-cloudtrail"
    }

@pytest.fixture(scope="function")
def _event_lambda_valid():
    return {
        "configRuleId": "config-rule-id",
        "version": "1.0",
        "configRuleName": "configRuleName",
        "configRuleArn": "arn:aws:config:ap-southeast-2:123456789012:config-rule/config-rule-id",
        "invokingEvent": "{\"awsAccountId\":\"123456789012\",\"notificationCreationTime\":\"2017-05-10T05:26:09.308Z\",\"messageType\":\"ScheduledNotification\",\"recordVersion\":\"1.0\"}",
        "resultToken": "NoResultToken",
        "eventLeftScope": False,
        "ruleParameters": "{\"testMode\": true}",
        "executionRoleArn": "arn:aws:iam::123456789012:role/aws-config-role",
        "accountId": "123456789012"
    }

#################################################################################
# Functions
#################################################################################
def _get_stubber(resp_trails, resp_trail_status, resp_event_selectors):
    b3_cloudtrail = boto3.client("cloudtrail")

    stubber = Stubber(b3_cloudtrail)
    stubber.add_response("describe_trails", resp_trails)
    stubber.add_response("get_trail_status", resp_trail_status)
    stubber.add_response("get_event_selectors", resp_event_selectors)

    return b3_cloudtrail, stubber

def _get_cloudtrail(stubber, b3_cloudtrail):
    stubber.activate()
    cloudtrail = CloudTrail(b3_cloudtrail)
    stubber.deactivate()

    return cloudtrail

def _get_compliance_type(stubber, b3_cloudtrail):
    stubber.activate()
    compliance_type = get_compliance_type(b3_cloudtrail)
    stubber.deactivate()

    return compliance_type

#################################################################################
# Classes
#################################################################################
class TestCloudTrail(object):
    def test_is_settings_correct(self, _resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert cloudtrail.is_settings_correct

    def test_trails_empty(self, _resp_trails_empty, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_empty, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct

    def test_logging_false(self, _resp_trails_valid, _resp_trail_status_logging_false, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_valid, _resp_trail_status_logging_false, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct

    def test_multi_region_false(self, _resp_trails_multi_region_false, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_multi_region_false, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct

    def test_readwrite_type_read(self, _resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_readwrite_type_read):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_readwrite_type_read)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct

    def test_s3_bucket_blank(self, _resp_trails_s3_bucket_blank, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_s3_bucket_blank, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct


    def test_encrypt_log_files_true(self, _resp_trails_encrypt_log_files_true, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_encrypt_log_files_true, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct

    def test_log_file_validation_false(self, _resp_trails_log_file_validation_enabled_false, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_log_file_validation_enabled_false, _resp_trail_status_valid, _resp_event_selectors_valid)
        cloudtrail = _get_cloudtrail(stubber, b3_cloudtrail)

        assert not cloudtrail.is_settings_correct


class TestCheckCloudTrail(object):
    def test_compliant(self, _resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_valid, _resp_trail_status_valid, _resp_event_selectors_valid)
        compliance_type = _get_compliance_type(stubber, b3_cloudtrail)

        assert compliance_type == "COMPLIANT"

    def test_non_compliant_no_trails(self, _resp_trails_empty, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_empty, _resp_trail_status_valid, _resp_event_selectors_valid)
        compliance_type = _get_compliance_type(stubber, b3_cloudtrail)

        assert compliance_type == "NON_COMPLIANT"

    def test_non_compliant_incorrect_trail_configuration(self, _resp_trails_invalid, _resp_trail_status_valid, _resp_event_selectors_valid):
        b3_cloudtrail, stubber = _get_stubber(_resp_trails_invalid, _resp_trail_status_valid, _resp_event_selectors_valid)
        compliance_type = _get_compliance_type(stubber, b3_cloudtrail)

        assert compliance_type == "NON_COMPLIANT"
