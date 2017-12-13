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
import json
import base64
import pytest

import boto3
from botocore.config import Config

from python_lib.get_verification_rules import get_rules_raw
from python_lib.common import to_camel_case

# need to use a Citizen ARN so we can run the lambda and assume role
if "CITIZEN_ARN" in os.environ:
    CITIZEN_ARN = os.environ["CITIZEN_ARN"]
else:
    CITIZEN_ARN = ""

if "prefix" in os.environ:
    PREFIX = os.environ["prefix"]
else:
    PREFIX = ""

def _default_constructor(loader, tag_suffix, node):
    return ""

def describe_cf_lambda_functions():
    """Get list of all lambda functions in Watchmen Cloud Formation"""
    cf_lambda_functions_list = []
    raw_lambdas = get_rules_raw()

    for rule in raw_lambdas:
        cf_lambda_functions_list.append(PREFIX + to_camel_case(rule))

    return cf_lambda_functions_list

# change the default settings so we don't get a timeout when running long lambdas
B3_CONFIG = Config(read_timeout=300, retries={"max_attempts": 0})
B3_LAMBDA = boto3.client("lambda", config=B3_CONFIG, verify=False)

CF_LAMBDAS = describe_cf_lambda_functions()

@pytest.fixture(params=CF_LAMBDAS)
def lambda_function(request):
    return request.param

def test_config_lambda_function(lambda_function):
    # assume Config Lambda function names start with Check (with prefix)
    lambda_prefix = PREFIX + "Check"

    # if not a "Config Lambda" function
    if lambda_function[:len(lambda_prefix)] != lambda_prefix:
        pytest.skip("Not a Config Lambda function")

    # test payload
    payload = {
        "configRuleName": "ConfigRuleName",
        "resultToken": "NoResultToken",
        "accountId": "1234567890",
        "invokingEvent": "{\"awsAccountId\": \"1234567890\", \"notificationCreationTime\": \"2017-05-10T05:26:09.308Z\", \"messageType\": \"ScheduledNotification\", \"recordVersion\": \"1.0\"}",
        "ruleParameters": "{\"testMode\": true, \"executionRoleArn\": \"" + CITIZEN_ARN + "\"}"
    }

    response = B3_LAMBDA.invoke(FunctionName=lambda_function, LogType="Tail", Payload=json.dumps(payload))

    compliance_type_found = False

    # if the function returned an error
    if "FunctionError" in response:
        print "Lambda returned an error"
    else:
        lambda_results = base64.standard_b64decode(response["LogResult"]).split("\n")

        for lambda_result in lambda_results:
            if '"complianceType": "COMPLIANT"' in lambda_result or '"complianceType": "NON_COMPLIANT"' in lambda_result:
                compliance_type_found = True
                break

    assert compliance_type_found
