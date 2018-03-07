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
set -euo pipefail

PARENT_PATH=${PWD}

ZIP_FILES=${PARENT_PATH}/zip_files
[ -d ${ZIP_FILES} ] || mkdir ${ZIP_FILES}

zip_sub_folders()
{
    for path in $(ls -d $1/*/); do
        # if there is a 2nd parameter
        if [ $# -ge 2 ]
        then
            zip_folder $path $2
        else
            zip_folder $path
        fi
    done
}

zip_folder()
{
    # don't zip the common folder, ignore it
    if [ $(basename $1) == "common" ]
    then
        return
    fi

    cd $1

    # if there is a 2nd parameter
    if [ $# -ge 2 ]
    then
        # copy the "common" folder into the current folder
        cp -R $2 $(basename $2)
    fi

    rm -f cksum.txt

    zip_file="${ZIP_FILES}/$( basename $1 ).zip"
    zip -r9 $zip_file *

    # get a list of all files (within the current folder) with their checksum and place the results into a file
    find . -type f -exec cksum {} \; > cksum.txt

    # Get the checksum of the "results" file. The checksum should change if the contents of at least 1 of the files changes.
    # Not doing a checksum on the ZIP file because we get a different checksum each time.
    CKSUM=`cksum cksum.txt | awk '{print $1}'`
    echo "$zip_file has checksum = $CKSUM"

    mv $zip_file ${ZIP_FILES}/$( basename $1 ).${CKSUM}.zip

    rm -f cksum.txt

    if [ $# -ge 2 ]
    then
        # delete the "common" folder
        rm -rf $(basename $2)
    fi

    echo ""
}

zip_sub_folders ${PARENT_PATH}/reports
zip_sub_folders ${PARENT_PATH}/citizen_updates
zip_sub_folders ${PARENT_PATH}/elasticsearch
zip_folder ${PARENT_PATH}/proxy_lambda
zip_sub_folders ${PARENT_PATH}/verification_rules ${PARENT_PATH}/verification_rules/common

aws s3 sync ${ZIP_FILES}/ s3://${BUCKET_NAME_LAMBDA}/ --no-verify-ssl
