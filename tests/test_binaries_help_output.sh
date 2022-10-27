#!/usr/bin/env bash

set -e

# ensures that the +x py scripts in the parent dir are all able to run `SCRIPT -h` without exploding

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."
find *.py -type f -perm +111 -exec ./{} -h \;

echo ""
echo "ALL OK"
