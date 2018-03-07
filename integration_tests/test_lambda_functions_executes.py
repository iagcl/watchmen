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

import python_lib.get_verification_rules as verification_rules
import python_lib.common as common

# need to use a Citizen ARN so we can run the lambda and assume role
CITIZEN_ARN = os.environ.get("CITIZEN_ARN", "")
PREFIX = os.environ.get("prefix", "")

def describe_cf_lambda_functions():
    """Get list of all non-proxy lambda functions in Watchmen"""
    cf_lambda_functions_list = []
    rules_location = os.environ.get("RULES_LOCATION", "")

    if rules_location:
        raw_lambdas = verification_rules.get_rules_raw(rules_location.split(","))
    else:
        raw_lambdas = verification_rules.get_rules_raw()

    for rule in raw_lambdas:
        cf_lambda_functions_list.append(PREFIX + common.to_pascal_case(rule))

    return cf_lambda_functions_list

# change the default settings so we don't get a timeout when running long lambdas
B3_CONFIG = Config(read_timeout=300, retries={"max_attempts": 0})
B3_LAMBDA = boto3.client("lambda", config=B3_CONFIG, verify=False)

CF_LAMBDAS = describe_cf_lambda_functions()

@pytest.fixture(params=CF_LAMBDAS)
def lambda_function(request):
    return request.param

def get_compliance_type_result(response):
    compliance_type_found = False

    # If the response has an error
    if "FunctionError" in response:
        print "Lambda returned an error"
    else:
        lambda_results = base64.standard_b64decode(response["LogResult"]).split("\n")

        for lambda_result in lambda_results:
            if '"complianceType": "COMPLIANT"' in lambda_result or \
                    '"complianceType": "NON_COMPLIANT"' in lambda_result:
                compliance_type_found = True
                break

    return compliance_type_found

##################################
# Tests
##################################
def test_config_lambda_function(lambda_function):
    # assume Config Lambda function names start with Check (with prefix)
    lambda_prefix = PREFIX + "Check"

    # if not a "Config Lambda" function
    if lambda_function[:len(lambda_prefix)] != lambda_prefix:
        pytest.skip("Not a Config Lambda function")

    # test payload
    payload = {
        "citizen_exec_role_arn": CITIZEN_ARN,
        "config_event": {
            "configRuleName": "ConfigRuleName",
            "resultToken": "NoResultToken",
            "accountId": "1234567890",
            "invokingEvent": "{\"awsAccountId\": \"1234567890\", \"notificationCreationTime\": \"2017-05-10T05:26:09.308Z\", \"messageType\": \"ScheduledNotification\", \"recordVersion\": \"1.0\"}",
            "ruleParameters": "{\"testMode\": true}"
        }
    }

    response = B3_LAMBDA.invoke(
        FunctionName=lambda_function,
        LogType="Tail",
        Payload=json.dumps(payload)
    )

    assert get_compliance_type_result(response)
