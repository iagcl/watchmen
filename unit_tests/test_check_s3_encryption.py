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
import datetime
import json
import pytest
import boto3

from moto import mock_s3
from moto.sts import mock_sts
from verification_rules.check_s3_encryption.s3_encryption import S3Encryption

@pytest.fixture(scope="class")
def event_lambda_valid():
    return {
        "invokingEvent": "{\"awsAccountId\":\"123456789012\",\"notificationCreationTime\":\"2016-07-13T21:50:00.373Z\",\"messageType\":\"ScheduledNotification\",\"recordVersion\":\"1.0\"}",
        "ruleParameters": "{\"myParameterKey\":\"myParameterValue\"}",
        "resultToken": "myResultToken",
        "eventLeftScope": "false",
        "executionRoleArn": "arn:aws:iam::123456789012:role/config-role",
        "configRuleArn": "arn:aws:config:us-east-2:123456789012:config-rule/config-rule-0123456",
        "configRuleName": "periodic-config-rule",
        "configRuleId": "config-rule-6543210",
        "accountId": "123456789012",
        "version": "1.0"
    }

@pytest.fixture(scope="class")
def list_my_buckets():
    return {
        'Buckets':
        [
            {
                'CreationDate': datetime.datetime(2017, 6, 21, 6, 1, 22, tzinfo=None),
                'Name': 'mock-s3-bucket'
            }
        ]
    }

@pytest.fixture(scope="class")
def bucket(event_lambda_valid):
    buckets = list_my_buckets()["Buckets"]
    return buckets.pop()

@pytest.fixture(scope="class")
def encryption_bucket_policy():
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1494568847000",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::mock-s3-bucket/*",
                "Condition": {
                    "StringNotEquals": {
                        "s3:x-amz-server-side-encryption": "AES256"
                    }
                }
            },
            {
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::mock-s3-bucket/*",
                "Condition": {
                    "Null": {
                        "s3:x-amz-server-side-encryption": "true"
                    }
                }
            }
        ]
    }

class TestCheckS3Encryption(object):

    @pytest.mark.usefixtures('bucket', 'encryption_bucket_policy')
    @mock_s3
    def test_get_compliance_type_compliant_bucket(self, bucket, encryption_bucket_policy):
        client = boto3.client('s3', region_name='ap-southeast-2')
        client.create_bucket(Bucket=bucket["Name"])
        client.put_bucket_policy(Bucket=bucket["Name"], Policy=json.dumps(encryption_bucket_policy))

        encrypted_bucket_list = S3Encryption(client).get_encryp_comp_s3_bucket_list()

        compliance_output = "NON_COMPLIANT"

        if bucket["Name"] in encrypted_bucket_list:
            compliance_output = "COMPLIANT"

        assert compliance_output == 'COMPLIANT'

    @pytest.mark.usefixtures('bucket', 'encryption_bucket_policy')
    @mock_s3
    def test_get_compliance_type_non_compliant_bucket(self, bucket):
        client = boto3.client('s3', region_name='ap-southeast-2')
        client.create_bucket(Bucket=bucket["Name"])

        encrypted_bucket_list = S3Encryption(client).get_encryp_comp_s3_bucket_list()

        compliance_output = "NON_COMPLIANT"

        if bucket["Name"] in encrypted_bucket_list:
            compliance_output = "COMPLIANT"

        assert compliance_output == 'NON_COMPLIANT'

class TestS3Encryption(object):
    @pytest.mark.usefixtures('bucket', 'encryption_bucket_policy')
    @mock_s3
    def test_get_encryption_compliant_s3_bucket_list(self, bucket, encryption_bucket_policy):
        client = boto3.client('s3', region_name='ap-southeast-2')
        client.create_bucket(Bucket=bucket["Name"])
        client.put_bucket_policy(Bucket=bucket["Name"], Policy= json.dumps(encryption_bucket_policy))

        s3_bucket_list = S3Encryption(client)
        compliant_s3_bucket_list = s3_bucket_list.get_encryp_comp_s3_bucket_list()
        assert compliant_s3_bucket_list == ['mock-s3-bucket']

    @mock_s3
    def test_get_encryption_non_compliant_s3_bucket_list(self, bucket):
        client = boto3.client('s3', region_name='ap-southeast-2')
        client.create_bucket(Bucket=bucket["Name"])

        s3_bucket_list = S3Encryption(client)
        compliant_s3_bucket_list = s3_bucket_list.get_encryp_comp_s3_bucket_list()
        assert compliant_s3_bucket_list == [None]
