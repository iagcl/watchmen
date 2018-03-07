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
import common
import get_accounts
import get_checksum_zip
import get_external_cidr
import os

TEMPLATE_BASE = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/templates/citizen-update.tmpl"
TEMPLATE_DESTINATION = os.environ['LOCATION_CORE']+"/"+"watchmen_cloudformation/files/citizen-update.yml"

def get_bucket_policy_cf(accounts):
    bucket_policy_accounts = ""
    for account in accounts:
        if bucket_policy_accounts != "":
            bucket_policy_accounts += "\n"

        bucket_policy_accounts += "{}- \"{}\"".format(" " * 16, account)

    return bucket_policy_accounts

def main():
    citizen_update_cf = common.get_template(TEMPLATE_BASE).replace(
        "{{bucket_policy_accounts}}",
        get_bucket_policy_cf(get_accounts.get_accounts())
    ).replace(
        "{{update_citizen_stacks}}",
        get_checksum_zip.get_checksum_zip("update_citizen_stacks")
    ).replace(
        "{{external_cidr}}",
        get_external_cidr.get_external_cidr()
    )

    common.generate_file(TEMPLATE_DESTINATION, citizen_update_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()
