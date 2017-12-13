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
from common import generate_file, to_camel_case, get_temp

RULES_TEMP_BASE = "citizen_cloudformation/templates/citizen-rules-cfn.tmpl"
TEMP_DESTINATION = "citizen_cloudformation/files/citizen-rules-cfn.yml"

def get_rules_cf(rules):
    return reduce(lambda rule_cf, rule: get_rule_cf(rule_cf, rule), rules, "")

def get_rule_cf(rule_cf, rule):
    temp = \
"""
 {rule_name}:
   Type: AWS::Config::ConfigRule
   Properties:
     ConfigRuleName: !Sub "${Prefix}{rule_name}"
     Description: {rule_description}
     InputParameters:
       executionRoleArn: !Sub "arn:aws:iam::${AWS::AccountId}:role/${Prefix}Citizen"
     Source:
       Owner: CUSTOM_LAMBDA
       SourceDetails:
         -
           EventSource: aws.config
           MessageType: ScheduledNotification
           MaximumExecutionFrequency: TwentyFour_Hours
       SourceIdentifier: !Join ["", [!Sub "arn:aws:lambda:${AWS::Region}:", Ref: WatchmenAccount, ":function:", !Sub "${Prefix}{rule_name}"]]
"""
    rule_cf += temp.replace("{rule_name}", to_camel_case(rule.get('name'))) \
                   .replace("{rule_description}", rule.get('description'))
    return rule_cf

def main():
    citizen_rules_cfn = get_temp(RULES_TEMP_BASE).replace(
        "{{citizen_rules}}",
        get_rules_cf(get_rules())
        # get_rules_cf([{'description': 'Placeholder', 'name': 'check_root_access_keys' }])
    )
    generate_file(TEMP_DESTINATION, citizen_rules_cfn)

if __name__ == "__main__":
    main()
