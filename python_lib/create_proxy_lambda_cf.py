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
Creates the proxy lambda CloudFormation template.
"""
import common
import get_accounts
import get_checksum_zip
import os

RULE_TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/proxy-lambda.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/proxy-lambda.yml"

def get_accounts_permissions(accounts):
    """Generates a CloudFormation snippet containing the permission for each AWS account.

    Args:
        accounts: List of AWS account ids

    Returns:
        CloudFormation snippet
    """
    permissions = ""

    for account in accounts:
        template = \
"""  Permission{account}:
    Type: AWS::Lambda::Permission
    DependsOn: LambdaFunction
    Properties:
      FunctionName: !Ref LambdaFunction
      Action: lambda:InvokeFunction
      Principal: config.amazonaws.com
      SourceAccount: "{account}"

"""
        permissions += template.replace("{account}", account)

    return permissions

def main():
    """Main function"""
    template = common.get_template(RULE_TEMPLATE_BASE).replace(
        "{{proxy_lambda_zip}}",
        get_checksum_zip.get_checksum_zip("proxy_lambda")
    ).replace(
        "{{proxy_lambda_permissions}}",
        get_accounts_permissions(get_accounts.get_accounts())
    )

    common.generate_file(TEMPLATE_DESTINATION, template)

if __name__ == "__main__":
    main()
