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

import copy

#######################
## GENERAL FUNCTIONS ##
#######################


def filter_jsonl_input(jsonl_input: dict, subject: str = None, condition: str = None, task: str = None) -> dict:
    """
    Return all JSONL objects in the input which match the parameters given
        Inputs: list of JSONL dicts, values for subject, condition, and task
        Outputs: list of state transition dicts which pass filter
    """

    # A JSONL imported using a file_utils function will be indexed as "subject_condition_task"
    if subject:
        jsonl_input = {key: value for key, value in jsonl_input.items() if key.startswith(f"{subject}_")}
    if condition:
        jsonl_input = {key: value for key, value in jsonl_input.items() if f"_{condition}_" in key}
    if task:
        jsonl_input = {key: value for key, value in jsonl_input.items() if key.endswith(f"_{task}")}

    return jsonl_input


########################
## TIME-BASED METRICS ##
########################


def get_average_km_fraction(filtered_jsonl: dict) -> float:
    """
    Given a list of filtered JSONLs, calculate the average fraction of time spent in state "km_pull_activity".
    Either JSONL format works, as km_pull_total_time and task_total time are calculated for State Transition
    JSONLs during file load.
        Inputs: list of JSONLs with relevant subject/condition/task to be averaged
        Outputs: float representing average time of list
    """
    km_time_fractions = []
    for key, value in filtered_jsonl.items():
        fraction = value["km_pull_total_time"] / value["task_total_time"]
        km_time_fractions.append(fraction)
    return sum(km_time_fractions) / len(km_time_fractions)


def get_average_total_time(filtered_jsonl: dict) -> float:
    """
    Given a list of filtered JSONLs, calculate the average total time
    Either JSONL format works, as task_total time is calculated for State Transition
    JSONLs during file load.
        Inputs: list of JSONLs with relevant subject/condition/task to be averaged
        Outputs: float representing average total_time
    """
    times = []
    for key, value in filtered_jsonl.items():
        times.append(value["task_total_time"])
    return sum(times) / len(times)


def get_km_time_proportional_reduction(jsonl_input: dict, task: str) -> float:
    """
    Given a list of JSONLs and a task ID, calculate the knowledge management proportional
    time reduction for that task between prototype and the baseline. All times from any subject
    for a given task/condition combination will be averaged before the proportional
    reduction is calculated.
        Inputs: list of JSONLs in subject-task or state transition format, task ID
        Outputs: float representing km time proportional reduction
    """
    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="prototype", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No prototype data for task {task} in JSONL. Times are required from both prototype and baseline conditions."
        )
    prototype_average_km_fraction = get_average_km_fraction(filtered_jsonl)

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="baseline", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No baseline data for task {task} in JSONL. Times are required from both prototype and baseline conditions."
        )
    baseline_average_km_fraction = get_average_km_fraction(filtered_jsonl)

    # handle edge case when both Baseline and Prototype systems have zero KM time
    if baseline_average_km_fraction == 0 and prototype_average_km_fraction == 0:
        return 0  # zero implies that Baseline/Prototype system performed equally

    # handle edge case when Baseline has zero KM time OR the Prototype system has more than twice the KM time than the Baseline
    elif baseline_average_km_fraction == 0 or prototype_average_km_fraction > 2 * baseline_average_km_fraction:
        return -1  # -1 implies that Prototype spend twice as much KM time as Baseline or more

    # Return calculated value if no edge case is encountered
    return 1 - (prototype_average_km_fraction / baseline_average_km_fraction)


def get_prototype_time_relative_to_baseline_and_optimal(jsonl_input: dict, task: str, optimal_time: int) -> float:
    """
    Given a list of JSONLs, a task ID, and an optimal time, calculate where the Prototype
    time falls on a scale of baseline = 0 to optimal = 1 All times from any subject
    for a given task/condition combination will be averaged before the relative time
    is calculated.
        Inputs: list of JSONLs in subject-task or state transition format, task ID, optimal time in sec for task
        Outputs: float representing time relative to baseline and optimal
    """

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="prototype", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No prototype data for {task} in JSONL. Times are required from both prototype and baseline conditions."
        )
    prototype_average_time = get_average_total_time(filtered_jsonl)

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="baseline", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No baseline data for {task} in JSONL. Times are required from both prototype and baseline conditions."
        )
    baseline_average_time = get_average_total_time(filtered_jsonl)

    # if Prototype time is less than Baseline, report the Prototype percent time reduction from Baseline (0%) to expert time (100%)
    if prototype_average_time <= baseline_average_time:
        return 1 - ((prototype_average_time - optimal_time) / (baseline_average_time - optimal_time))

    # if Prototype time is more than Baseline, report the Prototype percent time increase from Baseline (0%) to twice baseline (-100%)
    else:
        return max(1 - (prototype_average_time / baseline_average_time), -1)


#########################
## SCORE-BASED METRICS ##
#########################


def get_average_failure_rate(filtered_jsonl: dict, max_score: int) -> float:
    """
    Given a list of filtered subject-task JSONLs, calculate the average failure rate
        Inputs: list of JSONLs with relevant subject/condition/task to be averaged, maximum score for task
        Outputs: float representing average failure rate of list
    """
    success_scores = []
    for key, value in filtered_jsonl.items():
        if "task_grade" in value:
            success_scores.append(value["task_grade"])
    average_success_score = sum(success_scores) / len(success_scores)

    average_failure_score = max_score - average_success_score
    average_failure_rate = average_failure_score / max_score

    return average_failure_rate


def get_proportional_task_failure_rate_reduction(jsonl_input: dict, task: str, max_score: int) -> float:
    """
    Given a list of JSONLs, a task ID, and a max score calculate the fractional reduction
    in the failure rate for that task between prototype and the baseline. All scores from any subject
    for a given task/condition combination will be averaged before the fractional
    reduction is calculated.
        Inputs: list of JSONLs in subject-task format, task ID, maximum score for task
        Outputs: float representing score proportional reduction
    """

    random_key = next(iter(jsonl_input))
    if "task_grade" not in jsonl_input[random_key]:
        raise TypeError("Input JSONL must be Subject-Task format in order to calculate increased score.")

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="prototype", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No prototype data for {task} in JSONL. Grades are required from both prototype and baseline conditions."
        )
    prototype_average_failure_rate = get_average_failure_rate(filtered_jsonl, max_score)

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="baseline", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No baseline data for {task} in JSONL. Grades are required from both prototype and baseline conditions."
        )
    baseline_average_failure_rate = get_average_failure_rate(filtered_jsonl, max_score)

    # handle edge cases when both Baseline and Prototype system rates have zero values
    if baseline_average_failure_rate == 0 and prototype_average_failure_rate == 0:
        return 0  # zero implies that Baseline/Prototype system performed equally

    # handle edge case where Baseline has zero failure rate, or when Prototype system fails more than twice the Baseline rate
    elif baseline_average_failure_rate == 0 or prototype_average_failure_rate > 2 * baseline_average_failure_rate:
        return -1  # -1 implies that prototype participants fail twice as often as baseline

    # Return calculated value if edge cases aren't encountered
    return 1 - (prototype_average_failure_rate / baseline_average_failure_rate)


def get_binarized_proportional_task_failure_rate_reduction(
    jsonl_input: dict, task: str, max_score: int, passing_score: float
) -> float:
    """
    Given a list of JSONLs, a task ID, a max score, and a passing score, calculate
    the fractional reduction in the failure rate for that task between prototype and the baseline.
    IMPORTANT: Before calculations occur, the task scores will be recast to either 0 (failing)
    or the maximum score (passing). The minimum passing score is passed as a parameter.
    All scores from any subject for a given task/condition combination will be averaged
    before the fractional reduction is calculated.
        Inputs: list of JSONLs in subject-task format, task ID, maximum score for task, passing score for task
        Outputs: float representing score proportional reduction
    """

    if passing_score == "":
        raise ValueError("Passing score must be numeric.")

    jsonl_input_copy = copy.deepcopy(jsonl_input)
    for key, value in jsonl_input_copy.items():
        if "task_grade" in value and passing_score:
            value["task_grade"] = max_score if value["task_grade"] >= passing_score else 0

    binarized_proportional_task_failure_rate_reduction = get_proportional_task_failure_rate_reduction(
        jsonl_input_copy, task, max_score
    )
    return binarized_proportional_task_failure_rate_reduction


######################
## COMBINED METRICS ##
######################


def get_productivity(filtered_jsonl: dict) -> float:
    """
    Given a list of filtered subject-task JSONLs, calculate the productivity
        Inputs: list of JSONLs with relevant subject/condition/task data
        Outputs: float representing points earned per minute spent
    """

    # Note that this function does not normalize scores to 0-100 range
    # In order to compare scores across systems, normalization should be performed first.

    # Iterate through values and collect the scores and times
    scores_sum = 0
    times_sum = 0
    for key, value in filtered_jsonl.items():
        scores_sum += value["task_grade"]
        times_sum += value["task_total_time"] / 60

    # Avoid divide by zero error
    if times_sum == 0:
        raise ValueError("Sum of times for task is zero.")

    # Return points per minute
    return scores_sum / times_sum


def get_proportional_increase_in_productivity(jsonl_input: dict, task: str) -> float:
    """
    Given a list of JSONLs and a task ID, calculate the proportional
    increase in productivity for that task between prototype and the baseline.
        Inputs: list of JSONLs in subject-task format, task ID
        Outputs: float representing proportional increase in productivity from baseline to prototype
    """

    random_key = next(iter(jsonl_input))
    if "task_grade" not in jsonl_input[random_key]:
        raise TypeError("Input JSONL must be Subject-Task format in order to calculate productivity.")

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="prototype", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No prototype data for task {task} in JSONL. Times are required from both prototype and baseline conditions."
        )
    prototype_productivity = get_productivity(filtered_jsonl)

    filtered_jsonl = filter_jsonl_input(jsonl_input, condition="baseline", task=task)
    if len(filtered_jsonl) <= 0:
        raise ValueError(
            f"No baseline data for {task} in JSONL. Grades are required from both prototype and baseline conditions."
        )
    baseline_productivity = get_productivity(filtered_jsonl)

    # Avoid divide by zero error
    if baseline_productivity == 0:
        return float("inf")

    return (prototype_productivity - baseline_productivity) / baseline_productivity
