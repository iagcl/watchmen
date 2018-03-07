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
Checks whether encryption is enabled on S3
RULE_DESCRIPTION: S3 buckets must have encryption enabled.
"""
import json
import boto3
import common.credential as credential
import common.evaluation as evaluation
import common.logger as logger
import common.rule_parameter as rule_parameter

from s3_encryption import S3Encryption

def lambda_handler(event, context):
    """
    Handler for executing lambda. Setup AWS Config Evaluation for each S3 Bucket.

    Args:
        event: Lambda Event
        context: Lambda Context
    Returns:
        None
    """
    citizen_exec_role_arn = event["citizen_exec_role_arn"]
    event = event["config_event"]

    logger.log_event(event, context, None, None)
    invoking_event = json.loads(event["invokingEvent"])

    rule_parameters = rule_parameter.RuleParameter(event)
    is_test_mode = rule_parameters.get("testMode", False)

    assumed_creds = credential.get_assumed_creds(boto3.client("sts"), citizen_exec_role_arn)

    config = boto3.client("config", **assumed_creds)
    s3_b3_client = boto3.client("s3", **assumed_creds)

    buckets = s3_b3_client.list_buckets()["Buckets"]
    encrypted_buckets = S3Encryption(s3_b3_client).get_encryp_comp_s3_bucket_list()

    evaluation.delete_evaluation_results(config, is_test_mode, event["configRuleName"])

    if buckets == []:
        eval_element = evaluation.EvaluationElement(
            event["accountId"],
            "AWS::::Account",
            "COMPLIANT",
            "No S3 Buckets detected",
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
    else:
        for bucket in buckets:
            compliance_type = "NON_COMPLIANT"
            if "Name" in bucket:
                if bucket["Name"] in encrypted_buckets:
                    annotation = "S3 Bucket has Encryption"
                    compliance_type = "COMPLIANT"
                else:
                    annotation = "S3 Bucket has No Encryption"
            else:
                annotation = "Invalid S3 bucket"

            eval_element = evaluation.EvaluationElement(
                bucket["Name"],
                "AWS::S3::Bucket",
                compliance_type,
                annotation,
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
