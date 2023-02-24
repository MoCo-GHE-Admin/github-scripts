#!/usr/bin/env python

import os
import subprocess
import sys

# get a list of all python executable files in the current directory
python_files = [
    f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(".py") and os.access(f, os.X_OK)
]

# TODO: show files to test

# TODO: set path

counter = 0
# loop through each python executable file and run it with the '-h' argument
for file in python_files:
    # construct the command to run
    cmd = f"./{file} -h"

    print()
    print(f"*** running '{cmd}'...")
    print()

    # run the command and capture the return code
    result = subprocess.run(cmd, shell=True)
    return_code = result.returncode
    print()

    # check if the return code is 0
    if return_code != 0:
        print(f"Error: {file} exited with return code {return_code}.")
        sys.exit(1)
    counter += 1

print()
print(f"*** ALL OK (checked {counter} files)")
