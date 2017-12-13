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
RULE_DESCRIPTION: CloudTrail must be enabled for Woodstock S3 bucket for all regions, all Read/Write events with log file validation enabled.
"""

import os
import sys
import json
import boto3

from cloudtrail import CloudTrail

# If the common folder is within the parent folder, add to system path.
# Otherwise, assume it's a subfolder.
PARENT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if os.path.isdir(os.path.join(PARENT_PATH, "common")):
    sys.path.insert(0, PARENT_PATH)

import common.credential as credential
import common.evaluation as evaluation
import common.logger as logger

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
    Returns:
        aws config put_evaluations object
    """
    logger.log_event(event, context, None, None)
    invoking_event = json.loads(event["invokingEvent"])
    rule_parameters = json.loads(event["ruleParameters"])

    is_test_mode = rule_parameters["testMode"] if "testMode" in rule_parameters else False
    arn = rule_parameters["executionRoleArn"] if "executionRoleArn" in rule_parameters else None

    assumed_creds = credential.get_assumed_creds(boto3.client("sts"), arn)
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
