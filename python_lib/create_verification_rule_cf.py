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
from get_accounts import get_accounts
from common import generate_file, get_temp

RULE_TEMP_BASE = "watchmen_cloudformation/templates/verification-rule.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/verification-rule.yml"

def get_rule_cf(accounts):
    rule_cf = \
"""  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Join [ "", [ !Ref Prefix , !Ref VerificationRule ] ]
      Description: !Join [ "", [ !Ref Prefix , !Ref VerificationRuleDescription ] ]              
      Environment:
        Variables:
          env_var:
            !If
              - HasVerificationRuleEnvironment
              - !Ref VerificationRuleEnvironment
              - !Ref "AWS::NoValue"            
      Handler: !Ref VerificationRuleHandler
      MemorySize: 256
      Timeout: 300
      Role: !Ref LambdaExecutionRole
      Code:
        S3Bucket: !Ref LambdaS3Bucket
        S3Key: !Ref VerificationRuleChecksum
      Runtime: python2.7

  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Join [ "", [ "/aws/lambda/", !Ref Prefix , !Ref VerificationRule] ]
      RetentionInDays: !Ref RetentionInDays
"""
    rule_cf += get_accounts_permission(accounts)
    return rule_cf

def get_accounts_permission(accounts):
    permission_cf = ""
    for account in accounts:
        temp = \
"""
  Permission{account}:
    Type: AWS::Lambda::Permission
    DependsOn: LambdaFunction
    Properties:
      FunctionName: !Join [ "", [ !Ref Prefix , !Ref VerificationRule ] ]
      Action: lambda:InvokeFunction
      Principal: config.amazonaws.com
      SourceAccount: "{account}"
"""
        permission_cf += temp.replace("{account}", account)
    return permission_cf

def main():
    verification_rule_cf = get_temp(RULE_TEMP_BASE).replace( # Update cf with with resources for each rule
        "{{verification_rule}}",
        get_rule_cf(get_accounts())
    )
    generate_file(TEMP_DESTINATION, verification_rule_cf)

if __name__ == "__main__":
    main()
