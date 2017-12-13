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
import re
import json
import ast
import boto3
from botocore.exceptions import ClientError

CITIZEN_TEMPLATE = "https://{}.s3.amazonaws.com/citizen-rules-cfn.yml"

def describe_stacks(b3_cloudformation):
    """return a list of stacks"""
    paginator = b3_cloudformation.get_paginator('describe_stacks')
    page_iterator = paginator.paginate()

    stacks = []
    for page in page_iterator:
        for stack in page['Stacks']:
            stacks.append(stack)
    return stacks

def get_citizen_stacks(stacks, prefix):
    """ Loop through all the stacks and return anything that resembles a citizen"""

    citizen_stacks = []

    for stack in stacks:
        deployed_citizen_version = None

        try:
            if "Description" in stack and \
                    (prefix == "" or prefix == stack["StackName"][:len(prefix)]):

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
                "StackId": stack["StackId"],
                "StackStatus" : stack["StackStatus"]
            }

            citizen_stacks.append(citizen_stack)

    return citizen_stacks

def get_assumed_creds(sts, arn):
    """assume the role for the arn and return the credentials"""

    if arn:
        try:
            credentials = sts.assume_role(
                RoleArn=arn,
                RoleSessionName="AssumeRoleSession1"
            )["Credentials"]

            result = {
                "aws_access_key_id": credentials['AccessKeyId'],
                "aws_secret_access_key": credentials['SecretAccessKey'],
                "aws_session_token": credentials['SessionToken']
            }

        except ClientError:
            result = {}
    else:
        result = {}

    return result

def print_lambda_details(event, context):
    """print the event and context details"""
    print event

    if context:
        print {
            "aws_request_id" : context.aws_request_id,
            "memory_limit_in_mb" : context.memory_limit_in_mb,
            "remaining_time_in_millis" : context.get_remaining_time_in_millis(),
            "invoked_function_arn" : context.invoked_function_arn,
            "function_name" :context.function_name,
            "function_version" : context.function_version
        }

def request_citizen_update(stackname, b3_cloudformation, bucket):
    """request an update to the citizen stack, return the response"""

    try:
        response = b3_cloudformation.update_stack(
            StackName=stackname,
            TemplateURL=CITIZEN_TEMPLATE.format(bucket),
            ResourceTypes=[
                'AWS::Config::ConfigRule'
            ],
            Parameters=[
                {
                    'ParameterKey': 'WatchmenAccount',
                    'UsePreviousValue': True
                },
                {
                    'ParameterKey': 'Prefix',
                    'UsePreviousValue': True
                }
            ]
        )
        return response

    except ClientError as client_error:
        print {"Error" : client_error}

def request_citizen_creation(stack_name, b3_cloudformation, prefix, bucket):
    """request a creation of the citizen stack, return the response"""
    try:
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        response = b3_cloudformation.create_stack(
            StackName=stack_name,
            TemplateURL=CITIZEN_TEMPLATE.format(bucket),
            ResourceTypes=[
                'AWS::Config::ConfigRule'
            ],
            Parameters=[
                {
                    'ParameterKey': 'WatchmenAccount',
                    'ParameterValue': account_id
                },
                {
                    'ParameterKey': 'Prefix',
                    'ParameterValue': prefix
                }
            ]
        ),
        return response

    except ClientError as client_error:
        print {"Error" : client_error}

def request_citizen_deletion(stack_name, b3_cloudformation):
    """request the deletion of the citizen stack, return the response"""
    try:
        response = b3_cloudformation.delete_stack(StackName=stack_name)
        return response

    except ClientError as client_error:
        print {"Error" : client_error}

def is_aws_account_id(account_id):
    """check account looks like an aws account id (12 digits)"""
    pattern = r"\d{12}"
    match = re.search(pattern, account_id)

    return match

def invoke_lambdas(message):
    """split the message into account id's and re-invoke this function for each"""
    dict_message = ast.literal_eval(message)
    prefix = dict_message["prefix"]
    accounts = dict_message["accounts"].split()  # convert the string of accounts into a python list
    bucket = dict_message["bucket"]

    b3_lambda = boto3.client('lambda') # create a lambda object so we can invoke lambda

    for account_id in accounts: # loop through the accounts and invoke ourselves
        if is_aws_account_id(account_id):
            try:
                response = b3_lambda.invoke(
                    FunctionName='{}CitizenUpdate'.format(prefix),
                    InvocationType='Event',
                    Payload=json.dumps({"prefix": prefix, "bucket": bucket, "accounts": account_id})
                )
                print {"Response" : response}

            except ClientError as client_error:
                print {"Error" : client_error}

        else:
            print {"Error" : account_id + " does not look like an AWS account id"}

def run_cloudformation_in_account(account_id, prefix, bucket):
    """assume role in the citizen account and run the cloudformation"""

    arn = "arn:aws:iam::{}:role/{}CitizenUpdate".format(account_id, prefix)
    assumed_creds = get_assumed_creds(boto3.client("sts"), arn)

    # if there are no credentials to assume
    if not assumed_creds:
        print {"Error" : "Cannot assume credentials '{}'".format(arn)}
        return

    b3_cloudformation = boto3.client("cloudformation", **assumed_creds)

    stacks = describe_stacks(b3_cloudformation)
    citizen_stacks = get_citizen_stacks(stacks, prefix)

    # if we have citizen stacks then we need to update them
    if citizen_stacks:
        for stack in citizen_stacks:
            print stack
            # if the stack is in an updatable state
            if stack["StackStatus"] in [
                    'CREATE_COMPLETE',
                    'UPDATE_COMPLETE',
                    'UPDATE_ROLLBACK_COMPLETE'
            ]:
                response = request_citizen_update(stack["StackName"], b3_cloudformation, bucket)
                print {"INFO" : response}

            # if it's not updatable
            elif stack["StackStatus"] in ['ROLLBACK_COMPLETE']:
                raise Exception("The Citizen stack has a status of 'ROLLBACK_COMPLETE' and will not be updated")

    # if we don't have citizen stacks then we should create one
    else:
        stackname = prefix + 'CitizenRules'
        response = request_citizen_creation(stackname, b3_cloudformation, prefix, bucket)
        print {"INFO" : response}

def lambda_handler(event, context):
    """handle the lamdba invocation"""
    print_lambda_details(event, context)

    # If the event is a dict and contains Records, it's from SNS (or a test)
    # and should have a list of accounts to update. We split this list, and
    # call ourselves.

    # If it's dict and does not contain Records it's a new request with a
    # single account so we need to assume the role in that account and update the cfn

    if isinstance(event, dict) and "Records" in event:
        # If the dict contains Records it is from SNS we want to get the account IDs
        # from the message and then re-invoke this function with those to trigger updates
        message = event['Records'].pop()['Sns']['Message']
        invoke_lambdas(message)

    # here we are being invoked with a single account ID
    # if it's a valid account run the cloudformation
    elif isinstance(event, dict) and "Records" not in event:
        prefix = event["prefix"]
        account_id = event["accounts"].split()[0]
        bucket = event["bucket"]

        if is_aws_account_id(account_id):
            run_cloudformation_in_account(account_id, prefix, bucket)

        else:
            print {"Error" : account_id + " does not look like an AWS account id"}

    else:
        # not sure how we got here, let's print the details for debugging
        print_lambda_details(event, context)
