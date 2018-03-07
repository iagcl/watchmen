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
import json
import boto3
import pytest
import datetime

from botocore.stub import Stubber

from verification_rules.check_s3_encryption.s3_encryption import S3Encryption

@pytest.fixture(scope="function")
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

@pytest.fixture(scope="function")
def encryption_bucket_policy():
    return\
        {
   'Policy': '{"Version":"2012-10-17","Statement":[{"Sid":"Stmt1494568847000","Effect":"Deny","Principal":"*","Action":"s3:PutObject","Resource":"arn:aws:s3:::mock-s3-bucket/*","Condition":{"StringNotEquals":{"s3:x-amz-server-side-encryption":"AES256"}}},{"Effect":"Deny","Principal":"*","Action":"s3:PutObject","Resource":"arn:aws:s3:::mock-s3-bucket/*","Condition":{"Null":{"s3:x-amz-server-side-encryption":"true"}}}]}'
    }

@pytest.fixture(scope="function")
def default_encryption():
    return {
   'ServerSideEncryptionConfiguration': {
      'Rules': [
         {
            'ApplyServerSideEncryptionByDefault': {
               'SSEAlgorithm': 'AES256'
            }
         }
      ]
   }
}
#################################################################################
# Functions
#################################################################################

class TestCheckS3Encryption(object):
    def test_encryption_compliant_bucket(self, list_my_buckets, encryption_bucket_policy, default_encryption):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
            stubber.add_response('list_buckets', list_my_buckets, {})
            stubber.add_response('get_bucket_policy', encryption_bucket_policy)
            stubber.add_response('get_bucket_encryption', default_encryption)


            stubber.activate()
            policy_encrypted_buckets = S3Encryption(s3).get_encryp_comp_s3_bucket_list()
            stubber.deactivate()

        if 'mock-s3-bucket' in policy_encrypted_buckets:
            compliance_output = "COMPLIANT"

        assert compliance_output == 'COMPLIANT'


    def test_encryption_noncompliant_bucket(self, list_my_buckets):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
                stubber.add_response('list_buckets', list_my_buckets, {})
                stubber.add_response('get_bucket_encryption', {})

                stubber.activate()
                policy_encrypted_buckets = S3Encryption(s3).get_encryp_comp_s3_bucket_list()
                stubber.deactivate()

        if 'mock-s3-bucket' not in policy_encrypted_buckets:
                compliance_output = "NONCOMPLIANT"

        assert compliance_output == 'NONCOMPLIANT'


    def test_get_s3_bucket_policy_statement(self, list_my_buckets, encryption_bucket_policy):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
                stubber.add_response('list_buckets', list_my_buckets, {})
                stubber.add_response('get_bucket_policy', encryption_bucket_policy)

                stubber.activate()
                policy_statements = S3Encryption(s3).get_s3_bucket_policy_statement('mock-s3-bucket')
                stubber.deactivate()

        assert policy_statements == json.loads(encryption_bucket_policy['Policy'])['Statement']


    def test_get_encr_policy_bucket_list_compliant(self, list_my_buckets, encryption_bucket_policy):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
                stubber.add_response('list_buckets', list_my_buckets, {})
                stubber.add_response('get_bucket_policy', encryption_bucket_policy)

                stubber.activate()
                policy_statements = json.loads(encryption_bucket_policy['Policy'])['Statement']

                encr_policy_bucket_list = S3Encryption(s3).get_encr_policy_bucket_list('mock-s3-bucket', policy_statements)

                stubber.deactivate()

        assert encr_policy_bucket_list == 'mock-s3-bucket'


    def test_get_encr_policy_bucket_list_non_compliant(self, list_my_buckets):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
                stubber.add_response('list_buckets', list_my_buckets, {})

                stubber.activate()
                policy_statements = []

                encr_policy_bucket_list = S3Encryption(s3).get_encr_policy_bucket_list('mock-s3-bucket', policy_statements)

                stubber.deactivate()

        assert encr_policy_bucket_list ==  None


    def test_get_default_encr_bucket_list(self, list_my_buckets, default_encryption):

        s3 = boto3.client('s3')

        with Stubber(s3) as stubber:
                stubber.add_response('list_buckets', list_my_buckets, {})
                stubber.add_response('get_bucket_encryption', default_encryption)

                stubber.activate()
                default_encr_bucket_list = S3Encryption(s3).get_default_encr_bucket_list('mock-s3-bucket')
                stubber.deactivate()

        assert default_encr_bucket_list == 'mock-s3-bucket'