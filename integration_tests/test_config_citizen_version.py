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
import datetime
import time
import boto3
import pytest
import pytz

def start_rule_invoke(b3_config,config_rule):
    b3_config.start_config_rules_evaluation(
        ConfigRuleNames=config_rule )

    return

def check_rule_invoke_success(b3_config,config_rule):
    current_time = datetime.datetime.now(pytz.utc)
    config_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
        ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']

    exit_loop_timer = time.time() + 180  #  Exit if invocation doesn't start before 3mins
    break_loop = False

    while not break_loop and config_rule_invoc_time < current_time:
        print "Invocation not started..."
        config_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']

        if time.time() >= exit_loop_timer:
                print "Invocation Timeout: Invocation did not complete within 3mins..."
                break_loop = True

    print "Invocation has started..."

    return

def check_rule_eval_success(b3_config,config_rule):
    config_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']
    config_rule_eval_time = b3_config.describe_config_rule_evaluation_status(
        ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulEvaluationTime']

    exit_loop_timer = time.time() + 180  #  Exit if Re-evaluation doesn't finish before 3mins
    break_loop = False

    while not break_loop and config_rule_eval_time < config_rule_invoc_time:
        print "Evaluation not completed..."
        config_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']
        config_rule_eval_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulEvaluationTime']

        if time.time() >= exit_loop_timer:
                print "Evaluation Timeout: Evaluation did not complete within 3mins"
                break_loop = True

    print "Evaluation has completed..."

    return

def get_rule_eval_status(b3_config,config_rule):
    config_rule_status = b3_config.describe_compliance_by_config_rule(
        ConfigRuleNames=config_rule)[u'ComplianceByConfigRules'][0][u'Compliance'][u'ComplianceType']

    return config_rule_status

### entry point ###
if os.environ['prefix']:
    PREFIX = os.environ['prefix']
else:
    PREFIX = ""

b3_config = boto3.client('config', verify=False)
config_rule = [PREFIX + 'CheckCitizenVersion']

start_rule_invoke(b3_config, config_rule)
check_rule_invoke_success(b3_config, config_rule)
check_rule_eval_success(b3_config, config_rule)

config_rule_status = get_rule_eval_status(b3_config, config_rule)

def test_exist_and_valid_in_aws():
    """Test to see if CF config rules exist in AWS Account"""
    assert config_rule_status == "COMPLIANT"
