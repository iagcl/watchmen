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

if os.environ['prefix']:
    PREFIX = os.environ['prefix']
else:
    PREFIX = ""

def default_constructor(loader, tag_suffix, node):
    if tag_suffix == '!Sub' and '${Prefix}' in node.value:
        return PREFIX + str((node.value).replace('${Prefix}', ''))

    return ""

def describe_cf_config_rules():
    """Get list of all config rules in Citizen Cloud Formation"""
    cf_config_rules_list = []
    rules_location = os.environ.get("RULES_LOCATION", "")

    if rules_location:
        raw_lambdas = get_rules_raw(rules_location.split(","))
    else:
        raw_lambdas = get_rules_raw()

    for rule in raw_lambdas:
        cf_config_rules_list.append(PREFIX + to_pascal_case(rule))

    return cf_config_rules_list

def describe_aws_config_rules():
    """Get list of all config rules for AWS Account"""
    b3_client_config = boto3.client('config', verify=False)
    paginator = b3_client_config.get_paginator('describe_config_rules')
    page_iterator = paginator.paginate()

    aws_config_rules_list = [] # Clear list

    for page in page_iterator:
        for aws_config_rule in page['ConfigRules']:
            aws_config_rule_name = str(aws_config_rule['ConfigRuleName'])
            aws_config_rules_list.append(aws_config_rule_name)

    return aws_config_rules_list

cf_config_rules = describe_cf_config_rules()
aws_config_rules = describe_aws_config_rules()

@pytest.fixture(params=cf_config_rules)
def each_config_rule(request):
    return request.param

def test_exists_in_aws(each_config_rule):
    """Test to see if CF config rules exist in AWS Account"""
    assert each_config_rule in aws_config_rules
