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

TEMP_BASE = "watchmen_cloudformation/templates/citizen-update.tmpl"
TEMP_DESTINATION = "watchmen_cloudformation/files/citizen-update.yml"

def get_bucket_policy_cf(accounts):
    bucket_policy_accounts = ""
    for account in accounts:
        if bucket_policy_accounts != "":
            bucket_policy_accounts += "\n"

        bucket_policy_accounts += "{}- \"{}\"".format(" " * 16, account)

    return bucket_policy_accounts

def main():
    citizen_update_cf = get_temp(TEMP_BASE).replace( # Update bucket policy with child account information
        "{{bucket_policy_accounts}}",
        get_bucket_policy_cf(get_accounts())
    ).replace( # Update CitizenUpdate lambda function with checksum details
        "{{update_citizen_stacks}}",
        get_checksum_zip("update_citizen_stacks")
    )
    generate_file(TEMP_DESTINATION, citizen_update_cf) # Creates the deployable CF file

if __name__ == "__main__":
    main()
