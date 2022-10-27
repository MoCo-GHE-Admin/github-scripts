#!/usr/bin/env bash

set -e

# ensures that the +x py scripts in the parent dir are all able to run `SCRIPT -h` without exploding

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
OS="$(uname)"

cd "$SCRIPT_DIR/.."
if [[ "$OS" == "Linux" ]]; then
        # ...
        find *.py -type f -executable -exec ./{} -h \;
elif [[ "$OS" == "Darwin" ]]; then
        # Mac OSX
        find *.py -type f -perm +111 -exec ./{} -h \;
else
        # Unknown.
        echo "ERROR: Unknown OS!"
        exit 1
fi


echo ""
echo "ALL OK"
