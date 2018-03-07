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

"""Facilitates checking S3 bucket policies for encryption"""

import json

from botocore.exceptions import ClientError

class S3Encryption(object):
    """
    Provides the list of S3 buckets that are compliant.
    Attributes:
      b3_s3_client: Boto3 S3 client.
    """
    def __init__(self, b3_s3_client):
        """Constructor"""
        self.client = b3_s3_client
        self.s3_bucket_list = self.client.list_buckets()['Buckets']

    def get_s3_bucket_policy_statement(self, s3_bucket_name):
        """Retrieves policies attached to specified S3 bucket

        Args:
            s3_bucket_name: S3 Bucket name
        Returns:
            Policy statement
        """
        try:
            s3_bucket_policy = self.client.get_bucket_policy(Bucket=s3_bucket_name)

        except:
            s3_bucket_policy = []

        if s3_bucket_policy == []:
            policy_statement = []
        else:
            policy_statement = json.loads(s3_bucket_policy['Policy'])['Statement']

        return policy_statement

    def get_default_encr_bucket_list(self, s3_bucket_name):
        """Verifies whether the bucket has default encryption enabled.

        Args:
            s3_bucket_name: Name of the S3 Bucket
        Returns:
            Name of the S3 Bucket if it has default encryption enabled. Catch exception when no "default encryption" exists on a bucket
        """
        try:
            default_encryption = self.client.get_bucket_encryption(Bucket=s3_bucket_name)

            return s3_bucket_name if 'ServerSideEncryptionConfiguration' in default_encryption else None

        except ClientError as e:   # Handle error when buckets have no 'default encryption'
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return None
            else:
                print "Unexpected error: %s" % e

    def get_encr_policy_bucket_list(self, s3_bucket_name, policy_statements):
        """Verifies whether the bucket has encryption policy enabled.

        Args:
            s3_bucket_name: Name of the S3 Bucket
            policy_statements: Policy attached to specified S3 Bucket
        Returns:
            Name of the S3 Bucket if it has encryption enabled.
        """
        if policy_statements != []:
            for policy_statement in policy_statements:
                try:
                    if 's3:PutObject' in policy_statement['Action'] and \
                            'Deny' in policy_statement['Effect'] and \
                            policy_statement['Condition']['StringNotEquals']['s3:x-amz-server-side-encryption'] == 'AES256':

                        return s3_bucket_name

                    elif 's3:PutObject' in policy_statement['Action'] and \
                            'Allow' in policy_statement['Effect'] and \
                            policy_statement['Condition']['StringEquals']['s3:x-amz-server-side-encryption'] == 'AES256':

                        return s3_bucket_name

                except:
                    return None
        else:
            return None

    def get_encryp_comp_s3_bucket_list(self):
        """Get the list of compliant S3 Buckets

        Returns:
            List of S3 buckets
        """
        compliant_s3_bucket_list = []

        for s3_bucket_name in self.s3_bucket_list:
            policy_statements = self.get_s3_bucket_policy_statement(s3_bucket_name['Name'])

            compliant_s3_bucket_list.append(
                self.get_encr_policy_bucket_list(s3_bucket_name['Name'], policy_statements)
            )

            compliant_s3_bucket_list.append(
                self.get_default_encr_bucket_list(s3_bucket_name['Name'])
            )

        return list(set([i for i in compliant_s3_bucket_list if i is not None]))