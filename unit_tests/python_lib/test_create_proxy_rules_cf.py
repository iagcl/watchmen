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
import os
from mock import patch

import python_lib.create_proxy_rules_cf as proxy_rules_cf

def test_get_env_vars_snippet():
    env_vars = {"key1": "value1", "key2": "value2"}
    result = proxy_rules_cf.get_env_vars_snippet(env_vars)

    assert 'key1: "value1"' in result
    assert 'key2: "value2"' in result

@patch("python_lib.get_checksum_zip.get_checksum_zip", return_value="")
def test_get_cloud_formation_snippet(mock_checksum_zip):
    assert "Type: AWS::Lambda::Function" in proxy_rules_cf.get_cloud_formation_snippet()

@patch("python_lib.get_checksum_zip.get_checksum_zip", return_value="")
def test_main(mock_checksum_zip):
    assert proxy_rules_cf.main(["", os.environ["LOCATION_CORE"] + "/verification_rules"]) is None
