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
AWS Lambda source code for check_cloudtrail
RULE_DESCRIPTION: CloudTrail must be enabled in all regions,for all Read/Write events with log file validation enabled.
"""
import json
import boto3
import common.credential as credential
import common.evaluation as evaluation
import common.logger as logger
import common.rule_parameter as rule_parameter

from cloudtrail import CloudTrail

def get_compliance_type(b3_cloudtrail):
    """Returns the compliance type i.e. Compliant or Non_Compliant

    Args:
        b3_cloudtrail: boto3 cloudtrail client

    Returns:
        "COMPLIANT" or "NON_COMPLIANT" string
    """
    cloudtrail = CloudTrail(b3_cloudtrail)

    if cloudtrail.is_settings_correct:
        result = "COMPLIANT"
    else:
        result = "NON_COMPLIANT"

    return result

def lambda_handler(event, context):
    """Entrypoint for lambda function.

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
    config = boto3.client("config", **assumed_creds)

    compliance_type = get_compliance_type(boto3.client("cloudtrail", **assumed_creds))

    eval_element = evaluation.EvaluationElement(
        event["accountId"],
        "AWS::::Account",
        compliance_type,
        "",
        invoking_event["notificationCreationTime"]
    )

    evaluation.put_log_evaluation(
        config,
        eval_element,
        event["resultToken"],
        is_test_mode,
        logger,
        event,
        context
    )
