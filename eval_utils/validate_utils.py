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

import hashlib
from datetime import datetime

########################
## GENERAL VALIDATION ##
########################

conditions = ["prototype", "baseline"]


def iso_str_as_datetime(iso_str: str) -> datetime:
    """
    Convert a string formatted as an ISO 8601 UTC timestamp to a python datetime object
    """
    try:
        datetime_obj = datetime.fromisoformat(iso_str)
        return datetime_obj
    except ValueError as err:
        raise ValueError(f"Input {iso_str} is not an ISO 8601 UTC Timestamp. {err}")


##################################
## SUBJECT/TASK JSON VALIDATION ##
##################################

subject_task_schema = {
    "subject_id": str | int,
    "condition": conditions,
    "task_id": str | int,
    "task_start_time": datetime,
    "task_total_time": float | int,
    "km_pull_total_time": float | int,
    "km_push_total_time": float | int,
    "task_grade": str | int | float,
    "corpus_knowledge_nugget_count": int,
    "expert_captured_knowledge_nugget_count": int,
    "nugget_content": list,
    "task_timeout": bool,
    "optional_content": dict,  # this field will be passed over in validation
}


def verify_all_subject_task_fields_present(subject_task_input: dict, line_no: str = "?", filename: str = "?") -> None:
    """
    Validate that all Subject-Task fields are present
        Input: Subject-Task dictionary
        Output: Nothing if success, raises error if an attribute is missing
    """

    for attr in subject_task_schema:
        if attr not in subject_task_input and attr != "optional_content":
            raise Exception(f"Attribute '{attr}' not found on line {line_no} of {filename}")


def type_check_subject_task_fields(subject_task_input: dict, line_no: str = "?", filename: str = "?") -> None:
    """
    Validate that all Subject-Task values are the correct type
        Input: Subject-Task dictionary
        Output: Nothing if success, raises error if a value is incorrect
    """

    for attr in subject_task_input:
        value = subject_task_input[attr]
        if attr == "condition":
            if value not in conditions:
                raise ValueError(f"{attr} is not one of {conditions} ({filename} line {line_no})")
        else:
            try:
                if not isinstance(value, subject_task_schema[attr]):
                    raise TypeError(f"{attr} is not type {subject_task_schema[attr]} ({filename} line {line_no})")
            except KeyError:
                continue


########################################
## STATE TRANSITIONS JSONL VALIDATION ##
########################################

state_ids = ["task_initialized", "task_execution", "km_push_activity", "km_pull_activity", "task_conclusion"]

state_transition_schema = {
    "subject_id": str | int,
    "condition": conditions,
    "task_id": str | int,
    "utc_timestamp": datetime,
    "state_id": state_ids,
    "optional_content": dict,  # this field will be passed over in validation
}

valid_state_transitions = [
    ("task_initialized", "task_execution"),
    ("task_initialized", "km_pull_activity"),
    ("task_initialized", "km_push_activity"),
    ("task_initialized", "task_conclusion"),
    ("task_execution", "task_execution"),
    ("task_execution", "km_push_activity"),
    ("km_push_activity", "task_execution"),
    ("km_push_activity", "km_pull_activity"),
    ("km_push_activity", "task_conclusion"),
    ("km_pull_activity", "km_push_activity"),
    ("km_pull_activity", "task_execution"),
    ("km_pull_activity", "task_conclusion"),
    ("task_execution", "km_pull_activity"),
    ("task_execution", "task_conclusion"),
]

initial_state_id = "task_initialized"


def verify_all_state_transition_fields_present(
    state_transition_input: dict, line_no: int = "?", filename: str = "?"
) -> None:
    """
    Validate that all State Transition fields are present in a JSON
        Input: State Transition dictionary, line number in original file
        Output: Nothing if success, error raised if an attribute is missing
    """
    for attr in state_transition_schema:
        if attr not in state_transition_input and attr != "optional_content":
            raise Exception(f"Attribute '{attr}' not found on line {line_no} of {filename}")


def type_check_state_transition_fields(state_transition_input: dict, line_no: int = "?", filename: str = "?") -> None:
    """
    Validate that all State Transition values are the correct type
        Input: State Transition dictionary, line number in original file
        Output: Nothing if success, error raised if a value is incorrect
    """
    for attr in state_transition_input:
        value = state_transition_input[attr]
        if attr == "state_id":
            if value not in state_ids:
                raise ValueError(f"{attr} on line {line_no} of {filename} is not one of {state_ids}")
        elif attr == "condition":
            if value not in conditions:
                raise ValueError(f"{attr} is not one of {conditions}")
        else:
            try:
                if not isinstance(value, state_transition_schema[attr]):
                    raise TypeError(f"{attr} on line {line_no} of {filename} is not type {state_transition_schema[attr]}")
            except KeyError:
                continue


def verify_timestamps_inorder(
    timestamp_1: datetime,
    timestamp_2: datetime,
    timestamp_1_line_no: int = "?",
    timestamp_2_line_no: int = "?",
    previous_state_id: str = "?",
    filename: str = "?",
) -> None:
    """
    Validate that timestamps occur sequentially
        Inputs: two datetimes and their line numbers
        Output: Nothing if the timestamps are sequential, error raised if not
    """
    if timestamp_1 >= timestamp_2 and previous_state_id != initial_state_id:
        raise ValueError(
            f"Timestamp on line {timestamp_2_line_no} of {filename} occurs before timestamp on line {timestamp_1_line_no}"
        )


def verify_state_transition_valid(
    state_id_1: str, state_id_2: str, state_id_1_line_no: int = "?", state_id_2_line_no: int = "?", filename: str = "?"
) -> None:
    """
    Validate that state transition between two lines is valid
        Inputs: two state ids and their line numbers
        Output: Nothing if the edge exists in valid_state_transitions, error raised if not
    """
    if (state_id_1, state_id_2) not in valid_state_transitions:
        raise ValueError(
            f"State transition between lines {state_id_1_line_no} and {state_id_2_line_no} of {filename} is not valid"
        )


def verify_first_state_is_task_initialized(
    state_transitions: list, subject_task_identifier: str, line_no: int = "?", filename: str = "?"
) -> None:
    """
    Validate that first state id in a subject/task pair is task_initialized
        Inputs: list of state transitions, line number in original file
        Outputs: Nothing if first state id is task_initialized, error raised if not
    """
    if state_transitions[0]["state_id"] != "task_initialized":
        raise ValueError(
            f"First state_id for {subject_task_identifier} must be 'task_initialized'. First entry occurs on line {line_no} of {filename}"
        )


def verify_last_state_is_task_conclusion(
    state_transitions: list, subject_task_identifier: str, line_no: int = "?", filename: str = "?"
) -> None:
    """
    Validate that last state id in a file is task_conclusion
        Inputs: list of state transitions, line number in original file
        Outputs: Nothing if last state id is task_conclusion, error raised if not
    """
    if state_transitions[-1]["state_id"] != "task_conclusion":
        raise ValueError(
            f"Last state_id for {subject_task_identifier} must be 'task_conclusion'. Last entry occurs on line {line_no} of {filename}"
        )


####################
## CSV VALIDATION ##
####################


def verify_column_names(column_names: list) -> None:
    """
    Validate that column names are correct and in correct order
        Inputs: list of column names
        Outputs: Nothing if column names are correct, error raised if not
    """
    required_column_names = ["task_id", "task_optimal_time_in_seconds", "task_maximum_score"]
    optional_column_names = ["task_passing_score"]

    missing_columns = list(set(required_column_names).difference(column_names))
    extra_columns = list(set(column_names).difference(required_column_names))

    for column in extra_columns:
        if column in optional_column_names:
            extra_columns.remove(column)

    if missing_columns:
        raise ValueError(
            f"Missing column(s) {missing_columns} in CSV metadata file. Required column names are: {required_column_names}. Optional column names are: {optional_column_names}."
        )
    if extra_columns:
        raise ValueError(
            f"Extra column(s) {extra_columns} in CSV metadata file. Required column names are: {required_column_names}. Optional column names are {optional_column_names}."
        )


def verify_row_types(row: list, row_no: int = "?") -> list:
    """
    Validate that row of csv contains correct types
        Inputs: Row from csv
        Outputs: Row converted to correct types, error raised if unable to do so
    """

    # task ID type check not necessary

    # task_optimal_time_in_seconds
    try:
        row[1] = float(row[1])
    except ValueError as err:
        raise ValueError(f"CSV metadata file line {row_no}: {err}")

    # task_maximum_score
    try:
        row[2] = int(row[2])
    except ValueError as err:
        raise ValueError(f"CSV metadata file line {row_no}: {err}")

    # task_passing_score (optional, so can be null)
    if len(row) > 3 and row[3]:
        try:
            row[3] = float(row[3])
        except ValueError as err:
            raise ValueError(f"CSV metadata file line {row_no}: {err}")

    return row
