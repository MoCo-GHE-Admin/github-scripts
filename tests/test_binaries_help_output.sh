#!/usr/bin/env bash

set -e

# ensures that the +x py scripts in the parent dir are all able to run `SCRIPT -h` without exploding

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
OS="$(uname)"

cd "$SCRIPT_DIR/.."
if [[ "$OS" == "Linux" ]]; then
        # use xargs to check result code of each command
        find *.py -type f -executable -print0 | xargs -0 -n1 -I {} bash -c ./{} -h
# Mac OSX
elif [[ "$OS" == "Darwin" ]]; then
        find *.py -type f -perm +111 -print0 | xargs -0 -n1 -I {} bash -c ./{} -h
else
        # Unknown.
        echo "ERROR: Unknown OS!"
        exit 1
fi


echo ""
echo "ALL OK"
