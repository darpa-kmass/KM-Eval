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

import argparse
from eval_utils.file_utils import *
from eval_utils.metrics_utils import *

"""
Python script to calculate evaluation metrics for a directory
    Inputs: -i <input directory path>, -o <output file path>
    Outputs: Evaluation metrics are printed
    Example usage: `python evaluate.py -i tests/test_input_files -o output_files/metrics.csv`
"""

# Parse command line arguments
parser = argparse.ArgumentParser(description="Python script to calculate evaluation metrics for a task")
parser.add_argument(
    "-i",
    "--input",
    help="Path to directory containing data",
    required=True,
)
parser.add_argument(
    "-o",
    "--output",
    help="Path to write CSV output to",
    required=True,
)
args = parser.parse_args()

try:
    jsonl_contents, csv_contents = load_directory(args.input)

    if os.path.exists(args.output):
        raise ValueError("Output file path already exists")

    with open(args.output, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",")

        # Add core metrics column names
        headers = [
            "task",
            "km_time_proportional_reduction",
            "prototype_time_relative_to_baseline_and_optimal",
            "proportional_task_failure_rate_reduction",
            "proportional_increase_in_productivity",
        ]

        # Check for optional column(s)
        calculate_binarized_proportional_task_failure_rate = False
        for key, value in csv_contents.items():
            if "task_passing_score" in value:
                headers.append("binarized_proportional_task_failure_rate")
                calculate_binarized_proportional_task_failure_rate = True
                break

        # Write headers to file
        csv_writer.writerow(headers)

        for task in csv_contents:
            # Core metrics
            km_time_proportional_reduction = get_km_time_proportional_reduction(jsonl_contents, task)
            relative_time = get_prototype_time_relative_to_baseline_and_optimal(
                jsonl_contents, task, csv_contents[task]["task_optimal_time_in_seconds"]
            )
            proportional_task_failure_rate_reduction = get_proportional_task_failure_rate_reduction(
                jsonl_contents, task, csv_contents[task]["task_maximum_score"]
            )
            proportional_productivity_increase = get_proportional_increase_in_productivity(jsonl_contents, task)
            row = [
                task,
                km_time_proportional_reduction,
                relative_time,
                proportional_task_failure_rate_reduction,
                proportional_productivity_increase,
            ]

            # Optional metrics
            if calculate_binarized_proportional_task_failure_rate:
                if "task_passing_score" in csv_contents[task] and csv_contents[task]["task_passing_score"]:
                    binarized_proportional_task_failure_rate_reduction = (
                        get_binarized_proportional_task_failure_rate_reduction(
                            jsonl_contents,
                            task,
                            csv_contents[task]["task_maximum_score"],
                            csv_contents[task]["task_passing_score"],
                        )
                    )
                    row.append(binarized_proportional_task_failure_rate_reduction)
                else:
                    row.append("")

            # Write metrics to file
            csv_writer.writerow(row)

except Exception as err:
    print(f"ERROR: {err}")
