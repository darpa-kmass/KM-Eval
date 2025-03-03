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
from eval_utils.summary_utils import directory_summary

"""
Python script to create a summary CSV for a directory
    Inputs: -i <input directory path>, -o <output filename>
    Outputs: Summary CSV at <output filename>
    Example usage: `python summary.py -i tests/test_input_files -o output_files/summary.csv
"""

# Parse command line arguments
parser = argparse.ArgumentParser(description="Python script to create a summary CSV from directory contents")
parser.add_argument(
    "-i",
    "--input",
    help="Path to directory to summarize",
    required=True,
)
parser.add_argument(
    "-o",
    "--output",
    help="Output file path",
    required=True,
)
args = parser.parse_args()

try:
    directory_summary(args.input, args.output)
except Exception as err:
    print(f"ERROR: {err}")
