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
Creates the ElasticSearch CloudFormation template.
"""
import os
import sys
import common
import get_checksum_zip
import get_external_cidr
import get_verification_rules

RULES_TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/elastic-search.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/elastic-search.yml"

def get_subscriptions_cf(rules):
    """Creates a CloudFormation template snippet for subscriptions based on the rules provided.

    Args:
        rules: List of rules used to create subscriptions for.

    Returns:
        Text containing a snippet of the CloudFormation template for subscriptions.
    """
    snippet = ""

    for rule in rules:
        template = \
"""  {rule_name}Subscription:
    Type: AWS::Logs::SubscriptionFilter
    DependsOn: CloudwatchLogsLambdaPermissions
    Condition: ShouldCreateSubscription
    Properties:
      LogGroupName: !Sub "/aws/lambda/${Prefix}{rule_name}"
      FilterPattern: ""
      DestinationArn: !GetAtt LogsToElasticsearch.Arn

"""

        snippet += template.replace(
            "{rule_name}",
            common.to_pascal_case(rule.get('name'))
        )

    return snippet

def main(args):
    """Opens a "template" file, substitutes values into it and then writes
    the contents to a new file.
    """
    # If no parameters were passed in
    if len(args) == 1:
        rules = get_verification_rules.get_rules()
    else:
        # Parameter contains paths, e.g. ./verification_rules,./folder1/verification_rules
        rules = get_verification_rules.get_rules(args[1].split(","))

    elasticsearch_cf = common.get_template(RULES_TEMPLATE_BASE).replace(
        "{{logs_to_elastic_search}}",
        get_checksum_zip.get_checksum_zip("logs_to_elastic_search")
    ).replace(
        "{{roll_indexes}}",
        get_checksum_zip.get_checksum_zip("roll_indexes")
    ).replace(
        "{{external_cidr}}",
        get_external_cidr.get_external_cidr()
    ).replace(
        "{{rules-subscriptions}}",
        get_subscriptions_cf(rules)
    )

    common.generate_file(TEMPLATE_DESTINATION, elasticsearch_cf)

if __name__ == "__main__":
    main(sys.argv)
