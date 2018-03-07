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
import os
import re
import time
from datetime import datetime
from datetime import timedelta

import boto3
import pytest
from citizen_lib.trigger_citizen_stack_update import get_canary_accounts

MAIN_CITIZEN_FILE = "citizen-rules-cfn.yml"
PREFIX = os.environ.get("prefix", "")
CITIZEN_S3_BUCKET = os.environ.get("CITIZEN_S3_BUCKET", "")

def get_main_citizen_version(bucket):
    citizen_template_stream = boto3.client("s3", verify=False).get_object(Bucket=bucket, Key=MAIN_CITIZEN_FILE)

    #we expect the version to be within the first 128 bytes, so lets only read that
    citizen_template_body = citizen_template_stream["Body"].read(750)
    citizen_template_stream["Body"].close()

    # We're looking for the version number like in the string below
    # Description: "Watchmen-Citizen Compliance Rules Version 0.21"
    # the (.+) matches any word and gets returned as the first match
    try:
        citizen_version = re.search(
            'Description: \"Watchmen-Citizen Compliance Rules Version (.+)\"',
            citizen_template_body
        ).group(1)

    except AttributeError:
        citizen_version = None

    return citizen_version

def get_assumed_creds(sts, arn):
    if arn:
        credentials = sts.assume_role(RoleArn=arn, RoleSessionName="AssumeRoleSession1")["Credentials"]

        result = {
            "aws_access_key_id": credentials['AccessKeyId'],
            "aws_secret_access_key": credentials['SecretAccessKey'],
            "aws_session_token": credentials['SessionToken']
        }
    else:
        result = {}

    return result

def describe_stacks(b3_cloudformation):
    paginator = b3_cloudformation.get_paginator('describe_stacks')
    page_iterator = paginator.paginate()

    stacks = []

    for page in page_iterator:
        for stack in page['Stacks']:
            stacks.append(stack)

    return stacks

def get_citizen_stacks(stacks, prefix):
    citizen_stacks = []

    for stack in stacks:
        deployed_citizen_version = None

        try:
            # Since these tests will be run against our Tech Auto accounts, I'm assuming the Citizen stack name (which points to Watchmen) will begin with Citizen.
            # There could be multiple Citizen stacks (especially in Non Prod), 1 pointing to Watchmen and the others could be test stacks (with prefixes in the name).
            # If the prefix is blank, we want to ignore the test stacks and only pick up the Citizen stack which is pointing to Watchmen.
            # The approach below is a way of doing this. At this point in time, I can't think of another cleaner, simpler solution.
            if "Description" in stack and \
                    ( \
                        (prefix == "" and stack["StackName"][:7] == "Citizen") or \
                        (len(prefix) >= 1 and prefix == stack["StackName"][:len(prefix)]) \
                    ):
                deployed_citizen_version = re.search(
                    'Watchmen-Citizen Compliance Rules Version (.+)',
                    stack["Description"]
                ).group(1)

        except AttributeError:
            deployed_citizen_version = None

        if deployed_citizen_version:
            citizen_stack = {
                "StackName": stack["StackName"],
                "Version": deployed_citizen_version,
                "StackId": stack["StackId"],
                "StackStatus" : stack["StackStatus"]
            }

            citizen_stacks.append(citizen_stack)

    return citizen_stacks

def account_updated(account, main_citizen_version):
    max_timeout = datetime.now() + timedelta(seconds=180)

    arn = "arn:aws:iam::{}:role/{}CitizenUpdate".format(account, PREFIX)

    assumed_creds = get_assumed_creds(boto3.client("sts", verify=False), arn)
    b3_cloudformation = boto3.client("cloudformation", verify=False, **assumed_creds)

    # while the time is within the timeout
    while datetime.now() <= max_timeout:
        stack_updated = False

        stacks = describe_stacks(b3_cloudformation)
        citizen_stacks = get_citizen_stacks(stacks, PREFIX)

        if citizen_stacks:
            stack_updated = True

            for citizen_stack in citizen_stacks:
                if main_citizen_version != citizen_stack["Version"] or \
                        citizen_stack["StackStatus"] not in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                    stack_updated = False

            if stack_updated:
                break

        time.sleep(5)

    return stack_updated

CANARY_ACCOUNTS = get_canary_accounts()

################################################################################
# Tests
################################################################################
@pytest.fixture(params=CANARY_ACCOUNTS)
def account(request):
    return request.param

def test_citizen_stack_installation(account):
    result = False

    main_citizen_version = get_main_citizen_version(CITIZEN_S3_BUCKET)

    if main_citizen_version:
        result = account_updated(account, main_citizen_version)
    else:
        print "Unable to find the version of the Citizen stack in bucket '{}', file '{}'".format(CITIZEN_S3_BUCKET, MAIN_CITIZEN_FILE)

    assert result
