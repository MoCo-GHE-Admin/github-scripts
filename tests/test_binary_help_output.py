#!/usr/bin/env python

import os
import pprint
import subprocess
import sys

# SUMMARY: gets a list of executable python files and runs them with -h and
#          ensures they all exit 0.

# get a list of all python executable files in the current directory
FILE_ENDING = ".py"
python_files = [
    f
    for f in os.listdir(".")
    if os.path.isfile(f) and f.endswith(FILE_ENDING) and os.access(f, os.X_OK)
]

# show header and info about run
print(
    """
 ____  ____  ____  ____    ____  __  __ _   __   ____  _  _
(_  _)(  __)/ ___)(_  _)  (  _ \(  )(  ( \ / _\ (  _ \( \/ )
  )(   ) _) \___ \  )(     ) _ ( )( /    //    \ )   / )  /
 (__) (____)(____/ (__)   (____/(__)\_)__)\_/\_/(__\_)(__/
 _  _  ____  __    ____     __   _  _  ____  ____  _  _  ____
/ )( \(  __)(  )  (  _ \   /  \ / )( \(_  _)(  _ \/ )( \(_  _)
) __ ( ) _) / (_/\ ) __/  (  O )) \/ (  )(   ) __/) \/ (  )(
\_)(_/(____)\____/(__)     \__/ \____/ (__) (__)  \____/ (__)
""".lstrip()  # noqa: W605
)

print(f"directory to inspect: {os.getcwd()}")
print(f"looking for executables with the following suffix: {FILE_ENDING}")
print(f"files identified to test ({len(python_files)}):")
pprint.pprint(python_files, indent=2)

# TODO: add option to set path?

counter = 0
total = len(python_files)
# loop through each python executable file and run it with the '-h' argument
for file in python_files:
    counter += 1
    # construct the command to run
    cmd = f"./{file} -h"

    print()
    print(f"*** {counter}/{total} running '{cmd}'...")
    print()

    # run the command and capture the return code
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    return_code = result.returncode
    print(result.stdout)

    # check if the return code is 0
    if return_code != 0:
        print(f"Error: {file} exited with return code {return_code}.")
        sys.exit(1)

print()
print(f"*** ALL OK (checked {counter} files)")
