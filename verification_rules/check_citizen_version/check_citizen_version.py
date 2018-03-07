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
AWS Lambda source code for check_citizen_version
RULE_DESCRIPTION: Checks to see if the deployed Citizen stack is up to date [Stack vXXX-CITIZEN-VERSION-XXX]
ENVIRONMENT_VARIABLES: BUCKET_NAME_DISTRIBUTION
"""
# To pass multiple environment variables use "ENVIRONMENT_VARIABLES: var1,var2,var3" above

import json
import os
import re
import boto3
import common.evaluation as evaluation
import common.logger as logger
import common.credential as credential
import common.rule_parameter as rule_parameter

def get_prod_citizen_version(b3_s3, citizen_s3_bucket):
    """Retrieves the version number of a CloudFormation template from a S3 bucket.

    Args:
        b3_s3: boto3 s3 client
        citizen_s3_bucket: S3 bucket name

    Returns:
        Prod citizen version string
    """
    # get the latest cloudformation template from s3
    prod_citizen_template_stream = \
        b3_s3.get_object(Bucket=citizen_s3_bucket, Key='citizen-rules-cfn.yml')

    # We expect the version to be within the first 750 bytes (license header text included),
    # so lets only read that.
    prod_citizen_template_body = prod_citizen_template_stream["Body"].read(750)
    prod_citizen_template_stream["Body"].close() #close the stream now we are done with it

    # We're looking for the version number like in the string below
    # Description: "Watchmen-Citizen Compliance Rules Version 0.21"
    # the (.+) matches any word and gets returned as the first match
    try:
        prod_citizen_version = re.search(
            'Description: \"Watchmen-Citizen Compliance Rules Version (.+)\"',
            prod_citizen_template_body
        ).group(1)

    except AttributeError:
        # we check for this later
        prod_citizen_version = None

    return prod_citizen_version

def get_citizen_stacks(stacks):
    """Loop through the active stacks and if the stack description looks like a citizen stack,
    add it to our list

    Args:
        stacks: all cloudformation stacks in account

    Returns:
        Stacks that are citizen stacks
    """

    citizen_stacks = []

    for stack in stacks:
        deployed_citizen_version = None

        try:
            if "Description" in stack:
                deployed_citizen_version = re.search(
                    'Watchmen-Citizen Compliance Rules Version (.+)',
                    stack["Description"]
                ).group(1)

        except AttributeError:
            deployed_citizen_version = None

        if deployed_citizen_version:
            citizen_stack = {
                "StackName": stack["StackName"],
                "Version": deployed_citizen_version,
                "StackId": stack["StackId"]
            }

            citizen_stacks.append(citizen_stack)

    return citizen_stacks

def describe_active_stacks(b3_cloudformation):
    """Gets all active stacks in the aws account

    Args:
        b3_cloudformation: boto3 cloudformation client

    Returns:
        All active stacks
    """
    paginator = b3_cloudformation.get_paginator('describe_stacks')
    page_iterator = paginator.paginate()

    active_stacks = []

    # The 'StackStatus' can be any of the following
    # we only want to include 'active' stacks
    # that is, stacks which aren't being deleted, or didn't fail to create
    # 'CREATE_IN_PROGRESS'|'CREATE_FAILED'|'CREATE_COMPLETE'|
    # 'ROLLBACK_IN_PROGRESS'|'ROLLBACK_FAILED'|'ROLLBACK_COMPLETE'|
    # 'DELETE_IN_PROGRESS'|'DELETE_FAILED'|'DELETE_COMPLETE'|
    # 'UPDATE_IN_PROGRESS'|'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'|'UPDATE_COMPLETE'|
    # 'UPDATE_ROLLBACK_IN_PROGRESS'|'UPDATE_ROLLBACK_FAILED'|
    # 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS'|'UPDATE_ROLLBACK_COMPLETE'|
    # 'REVIEW_IN_PROGRESS',

    for page in page_iterator:
        for stack in page['Stacks']:
            if stack["StackStatus"] not in [
                    'CREATE_FAILED',
                    'DELETE_IN_PROGRESS',
                    'DELETE_COMPLETE',
                    'DELETE_FAILED'
                ]:
                active_stacks.append(stack)

    return active_stacks

def lambda_handler(event, context):
    """Main function.

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

    credentials = credential.get_assumed_creds(boto3.client("sts"), citizen_exec_role_arn)

    b3_config = boto3.client('config', **credentials)
    b3_s3 = boto3.client('s3', **credentials)
    b3_cloudformation = boto3.client('cloudformation', **credentials)

    evaluation.delete_evaluation_results(
        b3_config,
        is_test_mode,
        event.get("configRuleName")
    )

    prod_citizen_version = get_prod_citizen_version(
        b3_s3,
        os.environ.get("BUCKET_NAME_DISTRIBUTION", "")
    )

    stacks = describe_active_stacks(b3_cloudformation)
    citizen_stacks = get_citizen_stacks(stacks)

    if prod_citizen_version is None: # we couldn't fetch the version from the s3 bucket
        message = "Unable to fetch the latest production version of the Citizen Template"
        logger.log_event(event, context, None, message)

    elif citizen_stacks == []: # if we can't find any citizen stacks the account in non-compliant
        eval_element = evaluation.EvaluationElement(
            event["accountId"],
            "AWS::::Account",
            "NON_COMPLIANT",
            "No Citizen stack found in account",
            invoking_event["notificationCreationTime"]
        )

        evaluation.put_log_evaluation(
            b3_config,
            eval_element,
            event["resultToken"],
            is_test_mode,
            logger,
            event,
            context
        )
    else:
        for citizen_stack in citizen_stacks:
            if citizen_stack["Version"] == prod_citizen_version:
                compliance_type = "COMPLIANT"

                annotation = "Citizen Stack version " + \
                    citizen_stack["Version"] + \
                    " is up to date"
            else:
                compliance_type = "NON_COMPLIANT"

                annotation = "Citizen Stack is out of date, found version " + \
                    citizen_stack["Version"] + \
                    ", the latest available version is " + \
                    prod_citizen_version + \
                    ". Please update this Citizen Stack."

            eval_element = evaluation.EvaluationElement(
                citizen_stack["StackId"],
                "AWS::CloudFormation::Stack",
                compliance_type,
                annotation,
                invoking_event["notificationCreationTime"]
            )

            evaluation.put_log_evaluation(
                b3_config,
                eval_element,
                event["resultToken"],
                is_test_mode,
                logger,
                event,
                context
            )
