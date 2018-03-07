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
import os
import sys
import get_verification_rules
import common

RULES_TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"citizen_cloudformation/templates/citizen-rules-cfn.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"citizen_cloudformation/files/citizen-rules-cfn.yml"

def get_rules_cf(rules):
    snippet = ""

    for rule in rules:
        template = \
"""  {rule_name}:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: !Sub "${Prefix}{rule_name}"
      Description: {rule_description}
      Source:
        Owner: CUSTOM_LAMBDA
        SourceDetails:
          -
            EventSource: aws.config
            MessageType: ScheduledNotification
            MaximumExecutionFrequency: TwentyFour_Hours
        SourceIdentifier: !Sub "arn:aws:lambda:${AWS::Region}:${WatchmenAccount}:function:${Prefix}ProxyLambda"

"""

        snippet += template.replace(
            "{rule_name}",
            common.to_pascal_case(rule.get('name'))
        ).replace(
            "{rule_description}",
            rule.get('description')
        )

    return snippet

def main(args):
    # If no parameters were passed in
    if len(args) == 1:
        rules = get_verification_rules.get_rules()
    else:
        # Parameter contains paths, e.g. ./verification_rules,./folder1/verification_rules
        rules = get_verification_rules.get_rules(args[1].split(","))

    citizen_rules_cfn = common.get_template(RULES_TEMPLATE_BASE).replace(
        "{{citizen_rules}}",
        get_rules_cf(rules)
    )

    common.generate_file(TEMPLATE_DESTINATION, citizen_rules_cfn)

if __name__ == "__main__":
    main(sys.argv)
