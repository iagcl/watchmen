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

import python_lib.create_elastic_search_cf as elastic_search_cf

def test_get_subscriptions_cf():
    rules = [
        {"name": "test_name_1", "description": "test_desc_1"},
        {"name": "test_name_2", "description": "test_desc_2"}
    ]

    result = elastic_search_cf.get_subscriptions_cf(rules)

    assert "TestName1Subscription" in result
    assert "TestName2Subscription" in result

@patch("python_lib.get_checksum_zip.get_checksum_zip", return_value="roll_indexes.123.zip")
def test_main(mock_checksum_zip):
    assert elastic_search_cf.main(["", os.environ["LOCATION_CORE"] + "/verification_rules"]) is None
