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
Creates the proxy rules CloudFormation template.
"""
import os
import sys
import common
import get_checksum_zip
import get_verification_rules

RULE_TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/proxy-rules.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/proxy-rules.yml"

def get_env_vars_snippet(env_vars):
    """Generates a Lambda CloudFormation snippet for the environment variables."""
    snippet = ""

    if env_vars:
        snippet = \
"""      Environment:
        Variables:
"""

        for key, value in env_vars.iteritems():
            snippet += '{}{}: "{}"\n'.format(" " * 10, key, value)

    return snippet

def get_cloud_formation_snippet(rules_location=None):
    """Generates a Lambda CloudFormation snippet for the proxy rules."""
    snippet = ""

    if rules_location is None:
        rules = get_verification_rules.get_rules()
    else:
        rules = get_verification_rules.get_rules(rules_location)

    for rule in rules:
        template = \
"""  Lambda{function_name}:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub "${Prefix}{function_name}"
      Description: {description}
      Handler: "{handler}"
      MemorySize: 512
      Timeout: 300
      Role: !Sub "arn:aws:iam::${AWS::AccountId}:role/${Prefix}Watchmen"
{env_vars}      Code:
        S3Bucket: !Ref LambdaS3Bucket
        S3Key: "{zip_file}"
      Runtime: python2.7

  LogGroup{function_name}:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub "/aws/lambda/${Prefix}{function_name}"
      RetentionInDays: !Ref RetentionInDays

"""

        snippet += template.replace(
            "{function_name}",
            common.to_pascal_case(rule["name"])
        ).replace(
            "{description}",
            rule["description"]
        ).replace(
            "{handler}",
            rule["name"] + ".lambda_handler"
        ).replace(
            "{zip_file}",
            get_checksum_zip.get_checksum_zip(rule["name"])
        ).replace(
            "{env_vars}",
            get_env_vars_snippet(rule["environment"])
        )

    return snippet

def main(args):
    """Main function"""
    # If no parameters were passed in
    if len(args) == 1:
        cloud_formation_snippet = get_cloud_formation_snippet()
    else:
        # Parameter contains paths, e.g. ./verification_rules,./folder1/verification_rules
        cloud_formation_snippet = get_cloud_formation_snippet(args[1].split(","))

    template = common.get_template(RULE_TEMPLATE_BASE).replace(
        "{{proxy_rules}}",
        cloud_formation_snippet
    )

    common.generate_file(TEMPLATE_DESTINATION, template)

if __name__ == "__main__":
    main(sys.argv)
