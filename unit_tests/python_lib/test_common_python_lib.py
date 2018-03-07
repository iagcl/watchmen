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
import shutil
import python_lib.common as common

TEST_PATH = "./test"
TEST_FILE = TEST_PATH + "/test.txt"
FILE_CONTENT = "Test"

#################################
# Common functions
#################################
def generate_test_file():
    if not os.path.exists(TEST_PATH):
        os.mkdir(TEST_PATH)

    with open(TEST_FILE, "w") as filer:
        filer.write(FILE_CONTENT)

#################################
# Unit tests
#################################
def test_generate_file_folder_missing():
    if os.path.exists(TEST_PATH):
        shutil.rmtree(TEST_PATH)

    result = common.generate_file(TEST_FILE, FILE_CONTENT) is None

    # Cleanup
    shutil.rmtree(TEST_PATH)

    assert result

def test_generate_file_file_exists():
    generate_test_file()

    result = common.generate_file(TEST_FILE, FILE_CONTENT) is None

    # Cleanup
    shutil.rmtree(TEST_PATH)

    assert result

def test_to_pascal_case():
    assert common.to_pascal_case("test_case") == "TestCase"

def test_to_snake_case():
    assert common.to_snake_case("TestCase") == "test_case"

def test_get_template():
    generate_test_file()
    file_content = common.get_template(TEST_FILE)

    # Cleanup
    shutil.rmtree(TEST_PATH)

    assert file_content == FILE_CONTENT
