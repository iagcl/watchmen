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

"""
AWS Lambda source code for check_root_account_mfa.
RULE_DESCRIPTION: The root account must have MFA enabled.
"""
import json
import boto3
import common.evaluation as evaluation
import common.logger as logger
import common.rule_parameter as rule_parameter
import common.credential as credential

def get_evaluation_elements(b3_iam, invoking_event):
    """Returns evaluation results for every invoking event.

    Args:
        b3_iam: boto3 iam client
        invoking_event: invoking lambda event

    Returns:
        List of evaluation elements
    """
    eval_elements = []
    root_mfa_status = b3_iam.get_account_summary()['SummaryMap']

    if root_mfa_status['AccountMFAEnabled']:
        eval_elements.append(
            evaluation.EvaluationElement(
                invoking_event["awsAccountId"],
                "AWS::::Account",
                "COMPLIANT",
                "MFA is enabled for Root account",
                invoking_event["notificationCreationTime"]
            )
        )
    else:
        eval_elements.append(
            evaluation.EvaluationElement(
                invoking_event["awsAccountId"],
                "AWS::::Account",
                "NON_COMPLIANT",
                "MFA is Not enabled for Root account",
                invoking_event["notificationCreationTime"]
            )
        )

    return eval_elements

def lambda_handler(event, context):
    """The Main function that AWS Lambda invokes when the service executes this code.

    Args:
        event: lambda event
        context: lambda context
    """
    citizen_exec_role_arn = event["citizen_exec_role_arn"]
    event = event["config_event"]

    logger.log_event(event, context, None, None)

    invoking_event = json.loads(event["invokingEvent"])

    parameter = rule_parameter.RuleParameter(event)
    is_test_mode = parameter.get("testMode", False)

    assumed_creds = credential.get_assumed_creds(boto3.client("sts"), citizen_exec_role_arn)

    b3_iam = boto3.client("iam", **assumed_creds)
    b3_config = boto3.client("config", **assumed_creds)

    evaluation.delete_evaluation_results(b3_config, is_test_mode, event["configRuleName"])

    eval_elements = get_evaluation_elements(b3_iam, invoking_event)

    for eval_element in eval_elements:
        evaluation.put_log_evaluation(
            b3_config,
            eval_element,
            event["resultToken"],
            is_test_mode,
            logger,
            event,
            context
        )
