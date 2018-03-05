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
import python_lib.get_checksum_zip as checksum_zip

TEST_NAME = "test"
ZIP_FILES = ["test.zip"]

def test_zip_list_empty():
    assert not checksum_zip.find_checksum_zip_file_name(TEST_NAME, [])

def test_zip_list_populated():
    assert checksum_zip.find_checksum_zip_file_name(TEST_NAME, ZIP_FILES)

def test_get_checksum_zip():
    if not os.path.exists(checksum_zip.ZIP_FOLDER):
        os.mkdir(checksum_zip.ZIP_FOLDER)

    assert not checksum_zip.get_checksum_zip(TEST_NAME)
