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
from common import get_temp, generate_file
from get_accounts import get_accounts
from get_checksum_zip import get_checksum_zip

TEMP_BASE = "watchmen_cloudformation/templates/reporting.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/reporting.yml"

def get_event_rule_cf(accounts): # Adds a CloudWatch resource for each child AWS account
    event_cf = ""
    for account in accounts:
        temp = \
"""
  GenerateComplianceReportCloudWatchEvent{account}:
    Type: AWS::Events::Rule
    DependsOn: GenerateComplianceReport
    Properties:
      Name: !Join [ "", [ !Ref Prefix , "GenerateComplianceReport", "-", "{account}" ] ]
      Description: Triggers the generate compliance report
      ScheduleExpression: "rate(1 day)"
      State: ENABLED
      Targets:
      - Id: "Target1"
        Arn: !GetAtt GenerateComplianceReport.Arn
        Input: !Sub "{\\"reportBucket\\": \\"${ReportS3Bucket}\\", \\"executionRoleArn\\": \\"arn:aws:iam::{account}:role/${Prefix}Citizen\\"}"

  GenerateCompliancePermission{account}:
    Type: AWS::Lambda::Permission
    DependsOn: GenerateComplianceReport
    Properties:
      FunctionName: !Join [ "", [ !Ref Prefix , "GenerateComplianceReport" ] ]
      Action: "lambda:InvokeFunction"
      Principal: "events.amazonaws.com"
      SourceArn: !GetAtt GenerateComplianceReportCloudWatchEvent{account}.Arn
"""
        event_cf += temp.replace("{account}", account)

    return event_cf

def main():
    reporting_cf = get_temp(TEMP_BASE).replace( # Update CF template with all CloudWatch events
        "{{event_rule}}",
        get_event_rule_cf(get_accounts())
    ).replace( # Update generate_compliance_report lambda function with checksum details
        "{{generate_compliance_report}}",
        get_checksum_zip("generate_compliance_report")
    )
    generate_file(TEMP_DESTINATION, reporting_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()
