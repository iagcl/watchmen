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
import boto3
import pytest

from python_lib.get_verification_rules import get_rules_raw
from python_lib.common import to_pascal_case

PREFIX = os.environ.get("prefix", "")

def describe_cf_lambda_functions():
    """Get list of all lambda functions in Watchmen"""
    cf_lambda_functions_list = []
    rules_location = os.environ.get("RULES_LOCATION", "")

    if rules_location:
        raw_lambdas = get_rules_raw(rules_location.split(","))
    else:
        raw_lambdas = get_rules_raw()

    for rule in raw_lambdas:
        cf_lambda_functions_list.append(PREFIX + to_pascal_case(rule))

    return cf_lambda_functions_list

def describe_aws_lambda_functions():
    """Get list of all lambda functions for AWS Account"""
    b3_client_lambda = boto3.client('lambda', verify=False)
    paginator = b3_client_lambda.get_paginator('list_functions')
    page_iterator = paginator.paginate()

    aws_lambda_functions_list = [] # Clear list

    for page in page_iterator:
        for aws_lambda_function in page['Functions']:
            aws_lambda_function_name = aws_lambda_function['FunctionName']
            aws_lambda_functions_list.append(str(aws_lambda_function_name))

    return aws_lambda_functions_list

cf_lambdas = describe_cf_lambda_functions()
aws_lambdas = describe_aws_lambda_functions()

@pytest.fixture(params=cf_lambdas)
def each_lambda_function(request):
    return request.param

def test_exist_in_aws(each_lambda_function):
    """Test to see if CF lambdas exist in AWS Account"""
    print each_lambda_function

    assert each_lambda_function in aws_lambdas
