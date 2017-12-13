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

RULES_TEMP_BASE = "watchmen_cloudformation/templates/es-subscriptions.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/es-subscriptions.yml"

def get_subscriptions_cf(rules):
    return "".join([get_subscription_cf(rule, index) for index, rule in enumerate(rules)])

def get_subscription_cf(rule, index):
    temp = \
"""
  {rule_name}Subscription:
    Type: AWS::Logs::SubscriptionFilter
    Properties:
      LogGroupName: !Join [ "", [ "/aws/lambda/", !Ref Prefix , "{rule_name}" ]]
      FilterPattern: ""
      DestinationArn: !Ref LogsToElasticsearch
"""
    return temp.replace("{rule_name}", to_camel_case(rule.get('name')))

def main():
    subscriptions_cf = get_temp(RULES_TEMP_BASE).replace( # Update cf with each rule subscription
        "{{rules-subscriptions}}",
        get_subscriptions_cf(get_rules())
    )
    generate_file(TEMP_DESTINATION, subscriptions_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()
