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
import datetime
import json
import boto3
import botocore

def log_event(watchmen_account, onboarded_citizen, context):
    log = {}

    if context:
        log["requestId"] = context.aws_request_id
        log["memoryLimit"] = context.memory_limit_in_mb
        log["remainingTime"] = context.get_remaining_time_in_millis()
        log["functionArn"] = context.invoked_function_arn
        log["functionName"] = context.function_name
        log["functionVersion"] = context.function_version

    if watchmen_account:
        if onboarded_citizen:
            log["onboarded_citizen"] = onboarded_citizen
        else:
            log["non_onboarded_citizen"] = watchmen_account

    print json.dumps(log)

def get_assumed_creds(sts, arn):
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
        except botocore.exceptions.ClientError as ex:
            # If a client error is thrown, then check that it was a AssumeRole error.
            # If it was a AssumeRole error, then the Citizen Stack does not exist.
            error_code = (ex.response['Error'])

            if 'Not authorized to perform sts:AssumeRole' in error_code['Message'] and \
                    error_code['Code'] == 'AccessDenied':
                result = {}
    else:
        result = {}

    return result

def lambda_handler(event, context):
    arn = event["executionRoleArn"] if "executionRoleArn" in event else None

    # Get the Watchmen account id from the onboarded watchmen executionRoleArn
    watchmen_account = arn.split("arn:aws:iam::", 1)[1].split(":", 1)[0] if arn else None

    assumed_creds = get_assumed_creds(boto3.client("sts"), arn)

    if assumed_creds:
        account_id = boto3.client("sts", **assumed_creds).get_caller_identity()["Account"]

        file_content = "AccountId,RuleName,Compliance,NonCompliantCount\n"

        for config_rule in get_config_rules(assumed_creds):
            file_content += "{},{},{},{}\n".format(account_id, config_rule["ConfigRuleName"],
                                                    config_rule["Compliance"]["ComplianceType"],
                                                    get_non_compliant_count(config_rule))

        filename = "compliance-report-{}-{}.csv".format(
            account_id,
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        )

        boto3.resource("s3").Object(event["reportBucket"], filename).put(Body=file_content)
        log_event(watchmen_account, account_id, context)
    else:
        log_event(watchmen_account, None, context)

def get_config_rules(assumed_creds):
    page_iterator = boto3.client(
        "config",
        **assumed_creds
    ).get_paginator('describe_compliance_by_config_rule').paginate()

    return reduce(aggregate_config_rules, page_iterator, [])

def get_non_compliant_count(config_rule):
    # begin with zero non compliant resources
    non_compliant_count = 0

    # if the rule is non_compliant we have at least 1 non compliant resource
    if config_rule["Compliance"]["ComplianceType"] == "NON_COMPLIANT":
        non_compliant_count = 1

        # if we have a count of compliance count use that for the count instead
        if "ComplianceContributorCount" in config_rule["Compliance"]:
            non_compliant_count = config_rule[
                "Compliance"
            ]["ComplianceContributorCount"]["CappedCount"]

            # if the compliance count is capped, add a + to our count to indicate this
            if config_rule["Compliance"]["ComplianceContributorCount"]["CapExceeded"]:
                non_compliant_count = str(non_compliant_count) + "+"

    return non_compliant_count

def aggregate_config_rules(config_list, page):
    for rules in page['ComplianceByConfigRules']:
        config_list.append(rules)
    return config_list
