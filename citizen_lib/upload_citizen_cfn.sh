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
#!/bin/bash
set -e

# Assign environment variable values if set , else use default values

CITIZEN_VERSION_MINOR=${CITIZEN_VERSION_MINOR:-"dev"}
CITIZEN_VERSION_MAJOR=${CITIZEN_VERSION_MAJOR:-"0"}
CITIZEN_S3_BUCKET=${CITIZEN_S3_BUCKET:-"watchmen-citizen-templates"}
CITIZEN_RULES=${CITIZEN_RULES:-"./citizen_cloudformation/files/citizen-rules-cfn.yml"}
CITIZEN_BOOTSTRAP=${CITIZEN_BOOTSTRAP:-"./citizen_cloudformation/files/citizen-bootstrap-cfn.yml"}

# Upload the citizen-bootstrap-cfn.yml and citizen-rules-cfn.yml to CITIZEN_S3_BUCKET
# CITIZEN-VERSION=CITIZEN_VERSION_MAJOR.CITIZEN_VERSION_MINOR

sed -i "s/XXX-CITIZEN-VERSION-XXX/${CITIZEN_VERSION_MAJOR}.${CITIZEN_VERSION_MINOR}/g" ${CITIZEN_RULES}
`which aws` s3 --no-verify-ssl cp ${CITIZEN_RULES} s3://${CITIZEN_S3_BUCKET}/citizen-rules-cfn.yml
`which aws` s3 --no-verify-ssl cp ${CITIZEN_RULES} s3://${CITIZEN_S3_BUCKET}/archive/citizen-rules-cfn_${CITIZEN_VERSION_MAJOR}.${CITIZEN_VERSION_MINOR}.yml
`which aws` s3 --no-verify-ssl cp ${CITIZEN_BOOTSTRAP} s3://${CITIZEN_S3_BUCKET}/citizen-bootstrap-cfn.yml