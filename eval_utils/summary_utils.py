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

import csv
import os
from eval_utils.file_utils import load_directory


def directory_summary(dir_name: str, output_filename: str) -> None:
    """
    Open a directory filled with JSONL and CSV files. Convert it all to a CSV summary file.
        Inputs: dir_name (str), output_filename (str)
        Outputs: None. CSV summary file created in new dir output_files/
    """

    dict_summary, csv_metadata = load_directory(dir_name)

    # if csv_metadata is empty, raise exception
    if csv_metadata == {}:
        raise Exception(f"There is no task_metadata.csv spreadsheet in your input directory:  {dir_name}")

    # Get column names to output to CSV. Most come from JSONL files. Task metadata is added
    # to each line according to task_id
    random_key = next(iter(dict_summary))
    column_names = [elem for elem in dict_summary[random_key]]
    random_key = next(iter(csv_metadata))
    task_metadata_column_names = [elem for elem in csv_metadata[random_key]]
    if "state_transitions" in column_names:
        column_names.remove("state_transitions")
    column_names.extend(task_metadata_column_names)

    if os.path.exists(output_filename):
        raise ValueError("Output file path already exists")

    if not os.path.isdir(os.path.dirname(output_filename)):
        raise Exception(f"Directory path {os.path.dirname(output_filename)} does not exist!")

    # Write to CSV
    with open(output_filename, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",")
        csv_writer.writerow(column_names)

        for entry in dict_summary:
            csv_row = []
            for column in column_names:
                if column in dict_summary[entry]:
                    csv_row.append(dict_summary[entry][column])
                elif column in task_metadata_column_names:
                    task = dict_summary[entry]["task_id"]
                    csv_row.append(csv_metadata[task][column])
                else:
                    csv_row.append("")
            csv_writer.writerow(csv_row)
