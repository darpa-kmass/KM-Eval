# KM-Eval

The following repository contains Python code that can be used to evaluate comparisons between a Prototype and a Baseline knowledge management system.  Input data to be used with this repository must conform to specific requirements, and must include both timing and grading information for a set of participants who have completed tasks while using both the Baseline and Prototype system.  Core metrics that will be calculated include the following:  _Reduce Task Failure Rate_, _Reduce Time on Task_, and _Percent Increase in Task Productivity_.

## Requirements

Python 3.11+. No extra packages required unless performing statistical analyses with statistics_utils.py (see requirements.txt)

## Documentation

Note that additional documentation can be seen in the ./docs folder:
- [./docs/KNOWLEDGE_MANAGEMENT_EVAL_SCHEMA_README.md](./docs/KNOWLEDGE_MANAGEMENT_EVAL_SCHEMA_README.md) provides requirements on how all evaluation input data must be formatted prior to being processed by this repo
- [./docs/KNOWLEDGE_MANAGEMENT_METRICS_README.md](./docs/KNOWLEDGE_MANAGEMENT_METRICS_README.md) provides details on all of the core knowledge management metrics, and how they are calculated in this repository

## Data Cleaning

Combine multiple subject-task .json files and state-transition .jsonl files into one subject-task .jsonl and one state-transition .jsonl file for simplified post-processing, then clean data (if an evaluation is specified). `<input_directory>` here should contain all of the raw JSON/JSONL files for each specific subject-task combination.

If the subject-task .json and state-transition .jsonl files are already cleaned and aggregated, this step can be skipped.

```
python data_cleaning.py -i <input_directory> -o <output_directory>
```

Example (with sample data):
```
python data_cleaning.py -i ./sample_data/ -o ./clean_data/
```

## Summarize

Create a CSV summary file with data from all files in a directory. `<directory_name>` should contain a single `state_transitions.jsonl`, `subject_task.jsonl`, and `task_metadata.csv` file.

Note: If there are any total time discrepancies between `subject_task.jsonl` and `state_transitions.jsonl` for a given subject-task, these will be printed as "WARNING" messages to the console. Such time discrepancies should be mitigated/corrected in the raw evaluation data.

```
python summary.py -i <directory_name> -o <output_csv_filename>
```
Example (with sample data):
```
python summary.py -i ./clean_data/ -o ./output/summary.csv
```

## Validate

Validate that an input file has been constructed correctly (note that `input_file` must be one of the aggregated, cleaned jsonl files that are output in the data cleaning step).

```
python validate.py -i <input_file>
```

## Evaluate

Calculate evaluation metrics from a set of files. Requires both JSONL data files and a CSV metadata file. `<directory_name>` should contain a single `state_transitions.jsonl`, `subject_task.jsonl`, and `task_metadata.csv` file.

Note: If there are any total time discrepancies between `subject_task.jsonl` and `state_transitions.jsonl` for a given subject-task, these will be printed as "WARNING" messages to the console. Such time discrepancies should be mitigated/corrected in the raw evaluation data.

```
python evaluate.py -i <directory_name> -o <output_filename>
```
Example (with sample data):
```
python evaluate.py -i ./clean_data/ -o ./output/evaluation.csv
```

## License

See [LICENSE](LICENSE.md) for license information.

## Acknowledgements

This software was created by the Johns Hopkins University Applied Physics Laboratory and funded by the DARPA Knowledge Management at Scale and Speed (KMASS) Program.

Approved for public release:  distribution is unlimited. 

The views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.

© 2024 The Johns Hopkins University Applied Physics Laboratory LLC
