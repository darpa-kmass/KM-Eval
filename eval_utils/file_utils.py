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

import json
import csv
import os
import copy
from eval_utils.validate_utils import *

# the acceptable time difference between calculated vs reported KM time
TIME_DIFFERENCE_THRESHOLD = 1


def load_directory(dir_name: str) -> tuple((dict, dict)):
    """
    Open a directory filled with JSONL and CSV files. Load all JSONL files into a
    single dict and all CSV files into a single dict.
        Inputs: dir_name (str)
        Outputs: JSONL contents (dict indexed as "subject_condition_task"), CSV
                 contents (indexed by task ID)
    """

    jsonl_contents = {}
    csv_metadata = {}
    dir_contents = os.listdir(dir_name)

    for filename in dir_contents:
        file_relative_path = os.path.join(dir_name, filename)
        file_ext = os.path.splitext(filename)[-1]

        if file_ext == ".jsonl":
            file_contents = load_jsonl_file(file_relative_path)
            for entry in file_contents:
                # New subject/condition/task, add to list
                if not entry in jsonl_contents:
                    jsonl_contents[entry] = file_contents[entry]
                    jsonl_contents[entry]["file_source"] = filename

                # This subject/condition/task has been seen before, check that matched values are the same
                else:
                    recorded_total_time = jsonl_contents[entry]["task_total_time"]
                    recorded_km_time = jsonl_contents[entry]["km_pull_total_time"]
                    recorded_file = jsonl_contents[entry]["file_source"]
                    new_total_time = file_contents[entry]["task_total_time"]
                    new_km_time = file_contents[entry]["km_pull_total_time"]
                    new_file = filename
                    if abs(recorded_total_time - new_total_time) > TIME_DIFFERENCE_THRESHOLD:
                        print(
                            f"WARNING: Detected conflicting task_total_time for {entry}. Found task_total_time of {recorded_total_time} in {recorded_file} and {new_total_time} in {new_file}."
                        )  # consider reverting this back to a raised ValueError
                    if abs(recorded_km_time - new_km_time) > TIME_DIFFERENCE_THRESHOLD:
                        print(
                            f"WARNING: Detected conflicting km_pull_total_time for {entry}. Found km_pull_total_time of {recorded_km_time} in {recorded_file} and {new_km_time} in {new_file}."
                        )  # consider reverting this back to a raised ValueError

                    # If math matches, record the subject-task version and add state_transitions to it
                    if "state_transitions" in jsonl_contents[entry] and "state_transitions" not in file_contents[entry]:
                        new_jsonl = file_contents[entry]
                        new_jsonl["state_transitions"] = jsonl_contents[entry]["state_transitions"]
                        jsonl_contents[entry] = new_jsonl
                        jsonl_contents[entry]["file_source"] = filename
                    elif "state_transitions" in file_contents[entry] and "state_transitions" not in jsonl_contents[entry]:
                        jsonl_contents[entry]["state_transitions"] = file_contents[entry]["state_transitions"]

                    # If the entries are the same type, raise error if they do not contain the same data
                    elif "state_transitions" in file_contents[entry] and "state_transitions" in jsonl_contents[entry]:
                        comparable_contents = copy.deepcopy(jsonl_contents[entry])
                        del comparable_contents["file_source"]
                        if file_contents[entry] != comparable_contents:
                            raise ValueError(
                                f"Detected two conflicting State Transitions sequences for {entry} in files {recorded_file} and {new_file}."
                            )
                    elif (
                        "state_transitions" not in file_contents[entry] and "state_transitions" not in jsonl_contents[entry]
                    ):
                        comparable_contents = copy.deepcopy(jsonl_contents[entry])
                        del comparable_contents["file_source"]
                        if file_contents[entry] != comparable_contents:
                            raise ValueError(
                                f"Detected two conflicting Subject Task entries for {entry} in files {recorded_file} and {new_file}."
                            )

        elif filename == "task_metadata.csv":
            file_contents = load_csv_file(file_relative_path)
            for entry in file_contents:
                csv_metadata[entry] = file_contents[entry]

    return jsonl_contents, csv_metadata


def load_jsonl_file(jsonl_filename: str) -> dict:
    """
    Open a Subject-Task JSONL or State Transitions JSONL, identify which it is,
    then call the appropriate function to load it into memory
        Inputs: jsonl_filename (str)
        Outputs: file contents (dict indexed as "subject_condition_task")
                 see examples in function docstrings
    """

    jsonl_file_types = ["Subject-Task", "State Transitions"]

    # Identify file type. Raise exception if unable to.
    with open(jsonl_filename) as jsonl_file:
        # Load first line of JSONL
        first_line = jsonl_file.readline()
        first_line_json = json.loads(first_line)

        # Try both file types and print errors to user for debugging
        try:
            verify_all_subject_task_fields_present(first_line_json, 1, jsonl_filename)
            file_type = jsonl_file_types[0]
        except Exception as err1:
            try:
                verify_all_state_transition_fields_present(first_line_json, 1, jsonl_filename)
                file_type = jsonl_file_types[1]
            except Exception as err2:
                raise Exception(
                    f"Could not identify JSONL file type of {jsonl_filename}.\nTried {jsonl_file_types[0]} format: {err1}.\nTried {jsonl_file_types[1]} format: {err2}."
                )

    # Once file type has been identified, pass file to appropriate reader
    if file_type == jsonl_file_types[0]:
        subject_tasks = load_subject_task_file(jsonl_filename)
        # If no error has been raised, file looks good
        return subject_tasks

    elif file_type == jsonl_file_types[1]:
        state_transitions = load_state_transitions_file(jsonl_filename)
        # If no error has been raised, file looks good
        return state_transitions


def save_jsonl(json_object_list, outfile_path):
    """Write a Content JSONL file

    Args:
        json_object_list (list): list of dictionaries defining JSONL content objects
        outfile_path (str): output file path
    """

    # check that outfile_path directory path exists
    if not os.path.isdir(os.path.dirname(outfile_path)):
        raise Exception(f"Directory path {os.path.dirname(outfile_path)} does not exist!")

    # write json list to outfile_path
    with open(f"{outfile_path}", "w") as outfile:
        for entry in json_object_list:
            json.dump(entry, outfile)
            outfile.write("\n")


def load_subject_task_file(jsonl_filename: str) -> dict:
    """
    Read in a Subject-Task JSONL
        Inputs: json_filename (str)
        Outputs: dictionary of dictionaries, indexed as "subject_condition_task". e.g.
            {
                "User1_prototype_Task1": {
                    "subject_id" : "User1",
                    "condition" : "prototype",
                    "task_id" : "Task1",
                    "task_start_time" : "",
                    "task_total_time" : "",
                    "km_pull_total_time" : "",
                    "km_push_total_time" : "",
                    "task_grade" : "",
                    "optional_content" : {}
                },
                "User1_Task2": ...
            }
    """
    subject_tasks = {}
    with open(jsonl_filename) as jsonl_file:
        line = jsonl_file.readline()
        line_no = 1
        while line:
            json_in = json.loads(line)

            # Run validation checks
            verify_all_subject_task_fields_present(json_in, line_no, jsonl_filename)
            json_in["task_start_time"] = iso_str_as_datetime(json_in["task_start_time"])
            type_check_subject_task_fields(json_in, line_no, jsonl_filename)
            subject_condition_task_identifier = f"{json_in['subject_id']}_{json_in['condition']}_{json_in['task_id']}"
            subject_tasks[subject_condition_task_identifier] = json_in

            line = jsonl_file.readline()
            line_no += 1

        return subject_tasks


def load_state_transitions_file(jsonl_filename: str) -> dict:
    """
    Read in a State Transitions JSONL
        Inputs: json_filename (str)
        Outputs: dictionary of dictionaries, indexed as "subject_condition_task". Includes
            calculation of task_total_time and km_pull_total_time across all state
            transitions. e.g.
            {
                "User1_prototype_Task1": {
                    "subject_id" : "",
                    "condition" : "",
                    "task_id" : "",
                    "task_start_time" : "",
                    "task_total_time" : "",
                    "km_pull_total_time" : "",
                    "km_push_total_time" : "",
                    "state_transitions": [
                        {
                            "subject_id": "",
                            "condition": "",
                            "task_id": "",
                            "utc_timestamp": "",
                            "state_id": "",
                            "optional_content": ""
                        },
                        ...
                    ]
                },
                "User1_prototype_Task2": ...
            }
    """

    # Keep track of most recently seen state from a subject/condition/task combo
    # Include timestamp, state_id, and line no
    # This allows more than one subject/condition/task combo to be in a JSONL
    subject_task_state = {}

    with open(jsonl_filename) as jsonl_file:
        # Load JSONL
        line = jsonl_file.readline()
        line_no = 1
        state_transitions = {}
        while line:
            json_in = json.loads(line)

            # Run validation checks on each line
            verify_all_state_transition_fields_present(json_in, line_no, jsonl_filename)
            json_in["utc_timestamp"] = iso_str_as_datetime(json_in["utc_timestamp"])
            type_check_state_transition_fields(json_in, line_no, jsonl_filename)

            # Run validation checks between sequential JSONs
            # Use subject_task_state to retrieve most recently seen JSON for the given subject/task pair
            subject_task_identifier = f"{json_in['subject_id']}_{json_in['condition']}_{json_in['task_id']}"
            if subject_task_identifier in subject_task_state:
                previous_state = subject_task_state[subject_task_identifier]
                verify_timestamps_inorder(
                    previous_state["utc_timestamp"],
                    json_in["utc_timestamp"],
                    previous_state["line_no"],
                    line_no,
                    previous_state["state_id"],
                    jsonl_filename,
                )
                verify_state_transition_valid(
                    previous_state["state_id"], json_in["state_id"], previous_state["line_no"], line_no, jsonl_filename
                )
            else:
                state_transitions[subject_task_identifier] = {
                    "subject_id": json_in["subject_id"],
                    "condition": json_in["condition"],
                    "task_id": json_in["task_id"],
                    "task_start_time": json_in["utc_timestamp"],
                    "task_total_time": 0.0,
                    "km_pull_total_time": 0.0,
                    "km_push_total_time": 0.0,
                    "state_transitions": [],
                }
                verify_first_state_is_task_initialized([json_in], subject_task_identifier, line_no, jsonl_filename)

            # If no errors, record output and state
            if subject_task_identifier in subject_task_state:
                previous_state = subject_task_state[subject_task_identifier]
                elapsed_time = (json_in["utc_timestamp"] - previous_state["utc_timestamp"]).total_seconds()
                state_transitions[subject_task_identifier]["task_total_time"] += elapsed_time
                if previous_state["state_id"] == "km_pull_activity":
                    state_transitions[subject_task_identifier]["km_pull_total_time"] += elapsed_time
                if previous_state["state_id"] == "km_push_activity":
                    state_transitions[subject_task_identifier]["km_push_total_time"] += elapsed_time

            state_transitions[subject_task_identifier]["state_transitions"].append(json_in)
            subject_task_state[subject_task_identifier] = {
                "utc_timestamp": json_in["utc_timestamp"],
                "state_id": json_in["state_id"],
                "line_no": line_no,
            }
            line = jsonl_file.readline()
            line_no += 1

        # Run validation check on last states
        for subject_task_identifier in state_transitions:
            transitions = state_transitions[subject_task_identifier]["state_transitions"]
            verify_last_state_is_task_conclusion(
                transitions, subject_task_identifier, subject_task_state[subject_task_identifier]["line_no"], jsonl_filename
            )

        return state_transitions


def load_csv_file(csv_filename: str) -> dict:
    """
    Read in a Task Metadata CSV
        Inputs: csv_filename (str)
        Outputs: dictionary indexed by task ID
            {
                "Task1": {
                    "task_optimal_time_in_seconds" : <time>,
                    "task_maximum_score" : <score>
                },
                "Task2": ...
            }
    """
    tasks = {}
    with open(csv_filename, newline="") as csvfile:
        task_metadata = csv.reader(csvfile)
        for i, row in enumerate(task_metadata):
            if i == 0:
                verify_column_names(row)
                column_names = row
            else:
                row = verify_row_types(row, i + 1)
                attributes = {}
                for j, col in enumerate(row):
                    if j == 0:
                        continue
                    else:
                        attributes[column_names[j]] = col
                tasks[row[0]] = attributes

    return tasks
