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
Proxy lambda used by AWS Config rules.

This lambda function acts as a gateway for the lambda verification rules.
"""
import os
import json
import boto3

def log_info(event, citizen_exec_role_arn):
    """Prints certain information to the console.

    Args:
        event: Lambda event
        citizen_exec_role_arn: The ARN of the "Citizen" role used for assuming credentials
    """
    log = event.copy()
    log.pop("resultToken")

    log["citizen_exec_role_arn"] = citizen_exec_role_arn

    print json.dumps(log)

def invoke_lambda(b3_lambda, event):
    """Invokes a lambda function.

    Args:
        b3_lambda: Lambda boto3 client
        event: Lambda event
    """
    citizen_exec_role_arn = "arn:aws:iam::{}:role/{}Citizen".format(
        event["accountId"],
        os.environ.get("PREFIX", "")
    )

    log_info(event, citizen_exec_role_arn)

    payload = {
        "config_event": event,
        "citizen_exec_role_arn": citizen_exec_role_arn
    }

    b3_lambda.invoke(
        FunctionName=event["configRuleName"],
        InvocationType="Event",
        Payload=json.dumps(payload)
    )

def lambda_handler(event, context):
    """Main function.

    Args:
        event: Lambda event
        context: Lambda context
    """
    invoke_lambda(boto3.client("lambda"), event)
