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
from mock import patch
import python_lib.create_proxy_lambda_cf as proxy_lambda_cf

def test_get_accounts_permissions():
    accounts = ["1", "2", "3"]
    result = proxy_lambda_cf.get_accounts_permissions(accounts)

    for account in accounts:
        assert 'SourceAccount: "{}"'.format(account) in result

@patch("python_lib.get_checksum_zip.get_checksum_zip", return_value="proxy_lambda.123.zip")
@patch("python_lib.get_accounts.get_accounts")
def test_main(mock_get_accounts, mock_checksum_zip):
    assert proxy_lambda_cf.main() is None
