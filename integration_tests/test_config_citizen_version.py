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
import time
import boto3
import pytest

from botocore.exceptions import ClientError

def start_rule_invoke(b3_config,config_rule):
    try:
        previous_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
        ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']

        b3_config.start_config_rules_evaluation(
                ConfigRuleNames=config_rule )

    except ClientError as e:  # Handle LimitExceededException. Exception thrown if an evaluation is in progress or if StartConfigRulesEvaluation API is triggered more than once per minute.
        if e.response['Error']['Code'] == 'LimitExceededException':
            print "Previous evaluation is in progress, Wait for 60sec"
            time.sleep(60)    # Wait for 60sec before triggering evaluation
            b3_config.start_config_rules_evaluation(
                ConfigRuleNames=config_rule)
        else:
            print "Unexpected error: %s" % e

    return previous_rule_invoc_time

def check_rule_invoke_success(b3_config,config_rule, previous_rule_invoc_time):

    current_rule_invoc_time = previous_rule_invoc_time

    exit_loop_timer = time.time() + 180  #  Exit if invocation doesn't start before 3mins
    break_loop = False


    while not (break_loop or current_rule_invoc_time > previous_rule_invoc_time):
        print "Invocation not started..."
        current_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
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
        config_rule_invoc_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulInvocationTime']
        config_rule_eval_time = b3_config.describe_config_rule_evaluation_status(
            ConfigRuleNames=config_rule)[u'ConfigRulesEvaluationStatus'][0][u'LastSuccessfulEvaluationTime']

        print "Evaluation not completed..."

        if time.time() >= exit_loop_timer:
                print "Evaluation Timeout: Evaluation did not complete within 3mins"
                break_loop = True

    print "Evaluation has completed..."

    return

def get_rule_eval_status(b3_config, config_rule):
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

previous_rule_invoc_time = start_rule_invoke(b3_config, config_rule)
check_rule_invoke_success(b3_config, config_rule, previous_rule_invoc_time)
check_rule_eval_success(b3_config, config_rule)

config_rule_status = get_rule_eval_status(b3_config, config_rule)

def test_exist_and_valid_in_aws():
    """Test to see if CF config rules exist in AWS Account"""
    assert config_rule_status == "COMPLIANT"
