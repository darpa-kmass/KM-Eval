"""
Copyright © 2024 The Johns Hopkins University Applied Physics Laboratory LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse, os
from eval_utils.file_utils import *
from eval_utils.validate_utils import *

"""
Python script to verify that an input file has been constructed correctly
    Inputs: -i <input file path>
    Outputs: Error or Success print statement
    Example usage: `python validate.py -i docs/sample_subject_task.jsonl`
"""

# Parse command line arguments
parser = argparse.ArgumentParser(description="Python script to verify that an input file has been constructed correctly")
parser.add_argument(
    "-i",
    "--input",
    help="Path to file to verify",
    required=True,
)
args = parser.parse_args()

file_ext = os.path.splitext(args.input)[-1]

try:
    # Validate Subject-Task or State Transitions JSONL
    if file_ext == ".jsonl":
        # Identify file type, validate, and load
        jsonl_input = load_jsonl_file(args.input)
        print(f"Success: {args.input} is a valid JSONL")

    elif file_ext == ".json":
        # read the JSON file that process the subject-task JSON
        with open(args.input, "r") as json_file:
            json_obj = json.load(json_file)

        # Run validation checks
        verify_all_subject_task_fields_present(json_obj, 1, args.input)
        json_obj["task_start_time"] = iso_str_as_datetime(json_obj["task_start_time"])  # set task_start_time as a datetime
        type_check_subject_task_fields(json_obj, 1, args.input)

        print(f"Success: {args.input} is a valid subject-task JSON")

    # Validate Task Metadata CSV
    elif file_ext == ".csv":
        csv_input = load_csv_file(args.input)
        print(f"Success: {args.input} is a valid CSV")

    else:
        raise TypeError("Unknown file type.  File must be one of following:  .json, .jsonl, or .csv")

except Exception as err:
    print(f"ERROR: {err}")
