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
import zipfile
import python_lib.zip_verification_rules as zip_verification_rules
import python_lib.common as common

TEST_FOLDER = "test"
TEST_PATH = "./" + TEST_FOLDER
TEST_FILE = TEST_PATH + "/test.txt"

##################################
# Common functions
##################################
def create_test_folder():
    if not os.path.exists(TEST_PATH):
        os.mkdir(TEST_PATH)

##################################
# Unit tests
##################################
def test_zipdir():
    zip_file = "tmp.zip"

    create_test_folder()
    common.generate_file(TEST_FILE, "Test")

    zip_verification_rules.zipdir(
        TEST_PATH,
        zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
    )

    result = os.path.isfile(zip_file)

    # Cleanup
    os.remove(zip_file)
    os.remove(TEST_FILE)

    assert result

def test_get_child_folders():
    create_test_folder()
    assert not zip_verification_rules.get_child_folders(TEST_PATH)

def test_get_checksum():
    create_test_folder()
    assert zip_verification_rules.get_checksum(".", TEST_FOLDER)

def test_zip_folder():
    create_test_folder()

    # Create zip folder
    if not os.path.exists(zip_verification_rules.ZIP_FILES_FOLDER):
        os.mkdir(zip_verification_rules.ZIP_FILES_FOLDER)

    assert zip_verification_rules.zip_folder(".", TEST_FOLDER, "123") is None

def test_zip_folders():
    sub_folder = TEST_PATH + "/folder1"

    create_test_folder()

    if not os.path.exists(sub_folder):
        os.mkdir(sub_folder)

    assert zip_verification_rules.zip_folders(TEST_PATH) is None

def test_main():
    assert zip_verification_rules.main() is None
