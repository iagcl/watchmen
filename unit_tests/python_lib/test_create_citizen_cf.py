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
import python_lib.create_citizen_cf as citizen_cf

def test_get_rules_cf():
    rules = [
        {"name": "test_name_1", "description": "test_desc_1"},
        {"name": "test_name_2", "description": "test_desc_2"}
    ]

    result = citizen_cf.get_rules_cf(rules)

    assert "TestName1:" in result
    assert "TestName2:" in result

def test_main():
    assert citizen_cf.main(["", os.environ["LOCATION_CORE"] + "/verification_rules"]) is None
