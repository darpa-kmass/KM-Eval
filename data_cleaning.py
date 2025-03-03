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

import os
import json
import shutil
import argparse
from eval_utils.file_utils import save_jsonl

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Python script to condense JSON/JSONL files into two single JSONL files; one for Subject-Tasks and one for Transitions"
)
parser.add_argument(
    "-i",
    "--input",
    help="Path to directory with JSONL/JSON files",
    required=True,
)
parser.add_argument(
    "-o",
    "--output",
    help="Output path for JSONL files",
    required=True,
)
args = parser.parse_args()

# lists to collect all JSON objects across subject-task and transition JSON/JSONL files
subject_task_jsons = []
state_transition_jsons = []

# loop through all files in input directory and combine into a single subject-task JSONL and state-transition JSONL
for input_file in os.listdir(args.input):
    # absolute file path
    input_file_path = os.path.join(args.input, input_file)

    # if .json file, read content as a dictionary
    if input_file_path.endswith(".json"):
        # load json object as dictionary
        with open(input_file_path, "r") as json_file:
            json_obj = json.load(json_file)

        subject_task_jsons.append(json_obj)

    # if .jsonl file, read each line as a dictionary and store in list
    elif input_file_path.endswith(".jsonl"):
        with open(input_file_path) as jsonl_file:
            # loop through each line of JSONL, store each object as a dict
            jsonl_line = jsonl_file.readline()
            while jsonl_line:
                json_obj = json.loads(jsonl_line)
                state_transition_jsons.append(json_obj)
                jsonl_line = jsonl_file.readline()

# write the results to JSONL files
save_jsonl(subject_task_jsons, os.path.join(args.output, "subject_task.jsonl"))
save_jsonl(state_transition_jsons, os.path.join(args.output, "state_transitions.jsonl"))

# copy the task_metadata.csv file to the output directory
task_metadata_filepath = os.path.join(args.input, "task_metadata.csv")
if os.path.exists(task_metadata_filepath):
    shutil.copyfile(task_metadata_filepath, os.path.join(args.output, "task_metadata.csv"))
else:
    print(f"NOTE: task_metadata.csv is required to process evaluation results.")
    print(f"Please re-run and add to {args.input}, or manually place in {args.output}")
