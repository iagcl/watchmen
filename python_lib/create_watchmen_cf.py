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
from get_verification_rules import get_rules
from get_checksum_zip import get_checksum_zip
from get_external_cidr import get_external_cidr
from get_notifications import get_notification_email, get_notification_slack, get_slack_channel_hook_url
from common import generate_file, to_camel_case, get_temp

RULES_TEMP_BASE = "watchmen_cloudformation/templates/watchmen.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/watchmen.yml"

def get_rules_cf(rules):
    return reduce(lambda rule_cf, rule: get_rule_cf(rule_cf, rule), rules, "")

def get_rule_cf(rule_cf, rule):
    temp = \
"""
  {rule_name}Stack:
    Type: "AWS::CloudFormation::Stack"
    Properties:
      Parameters:
        Prefix: !Ref Prefix
        LambdaExecutionRole: !GetAtt RolesStack.Outputs.LambdaExecutionRole
        LambdaS3Bucket: !Ref LambdaS3Bucket
        VerificationRule: "{rule_name}"
        VerificationRuleHandler: "{rule_name_snake_case}.lambda_handler"
        VerificationRuleChecksum: "{rule_checksum}"
        VerificationRuleEnvironment: '{rule_environment}'
        VerificationRuleDescription: '{rule_description}'
      TemplateURL: !Sub "https://s3.amazonaws.com/${CloudFormationS3Bucket}/verification-rule.yml"
"""
    rule_cf += temp.replace("{rule_name}", to_camel_case(rule.get('name'))) \
        .replace("{rule_name_snake_case}", rule.get('name')) \
        .replace("{rule_checksum}", get_checksum_zip(rule.get('name'))) \
        .replace("{rule_environment}", rule.get('environment')) \
        .replace("{rule_description}", rule.get('description'))

    return rule_cf

def main():
    verification_rule_cf = get_temp(RULES_TEMP_BASE).replace( # Update cf with each rule stack
        "{{verification_rules}}",
        get_rules_cf(get_rules())
    ).replace( # Update S3 bucket policy to only allow access from company's IP address range
        "{{external_cidr}}",
        get_external_cidr()
    ).replace(
        "{{notifications_slack}}",
        get_notification_slack()
    ).replace(
        "{{slack_channel_hook_url}}",
        get_slack_channel_hook_url()
    ).replace(
        "{{notifications_email}}",
        get_notification_email()
    )
    generate_file(TEMP_DESTINATION, verification_rule_cf)

if __name__ == "__main__":
    main()