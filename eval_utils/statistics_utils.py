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

import numpy as np
from math import ceil, sqrt
import matplotlib.pyplot as plt
from statsmodels.stats.power import TTestIndPower
from scipy.stats import mannwhitneyu, ttest_ind


def estimate_t_test_effect_size(prototype_mean, baseline_mean, prototype_std_dev, baseline_std_dev):
    """Function to quantify effect size via Cohen's D Statistic for independent Welch T-test effect size; this calculation assumes 2 degree of freedom

    Effect size is a variable that must be assumed when calculating for necessary sample size in a t-test power analysis, it
    represents the effect (or difference) expected to be seen between the Prototype system and baseline

    Args:
        prototype_mean (float):  Prototype system mean estimate
        baseline_mean (float):  Baseline system mean estimate
        prototype_std_dev (float):  Prototype system standard deviation estimate
        baseline_std_dev (float):  Baseline system standard deviation estimate

    Returns:
        float: effect size estimate
    """

    # calculate mean difference and pooled standard deviation for Welch's independent t-test
    mean_difference = prototype_mean - baseline_mean
    pooled_standard_deviation = sqrt((prototype_std_dev ^ 2 + baseline_std_dev ^ 2) / 2)

    # calculate and return Cohen's D statistic
    cohens_d_stat = mean_difference / pooled_standard_deviation

    return cohens_d_stat


def estimate_t_test_required_sample_size(alpha, power, effect_size, alternative="larger", print_result=True):
    """Estimate the required samples sizes for a given alpha, power, and effect_size (assuming an independent 2-sample, one-sided t-test)

    Args:
        alpha (float): significance level, or the probability of type I error, where we'd incorrectly reject the Null Hypothesis
            even though it is true (typically we set this 0.05)
        power (float):  the power of the test, or 1 minus the probability of type II error, representing the probability that we reject
            the null hypothesis if the alternative hypothesis is true (common value for this is 0.8)
        effect_size (float):  the standardized effect size for a 2-sample Welsh's T-test (should be Cohen's D statistic)
        alternative (str):  specifies what type of 1-sided t-test to conduct ('larger' => Prototype value larger than Baseline,
            'smaller' => Prototype value lesser than Baseline)

    Returns:
        int: the estimated required sample/participant count
    """

    # initialize T-test power calculator from statmodels
    ttest_power_obj = TTestIndPower()

    # solve for power, return ceiling of result since we want an integer value
    result = ttest_power_obj.solve_power(effect_size=effect_size, power=power, alpha=alpha, alternative=alternative)
    result = ceil(result)

    # (optionally) print and return result
    if print_result:
        print("Sample Size:", result)
    return result


def display_t_test_power_curve(
    alpha=0.05,
    effect_sizes=[0.5, 0.8, 1.0, 1.5, 2.0, 3.0],
    min_num_samples=2,
    max_num_samples=50,
    alternative="larger",
):
    """Display the statistical power curve for a given alpha, range of samples sizes, and effect sizes (assume an indep. 2-sample, one-sided t-test)

    Args:
        alpha (float):  significance level, or the probability of type I error, where we'd incorrectly reject the Null Hypothesis
            even though it is true (typically we set this 0.05)
        effect_size (list):  list standard effect sizes for a 2-sample Welsh's T-test (Cohen's D statistic) to include in result power curve figure
        min_num_samples (int):  minimum number of samples show in power curve
        max_num_samples (int):  maximum number of samples to show in power curve
        alternative (str):  specifies what type of 1-sided t-test to conduct ('larger' => Prototype value should be larger than Baseline in Alt Hypothesis,
            'smaller' => Prototype value should be lesser than Baseline in Alt Hypothesis)

    Returns:
        matplotlib.figure.Figure: a matplotlib figure with the Power curves
    """

    # convert effect size list and sample sizes to a np.array
    effect_sizes = np.array(effect_sizes)
    sample_sizes = np.array(range(min_num_samples, max_num_samples))

    # Create an axis with gridlines
    _, ax = plt.subplots()
    ax.grid(True)

    # generate power curves via statmodels TTestIndPower.plot_power() function
    ttest_power_obj = TTestIndPower()
    plt_fig = ttest_power_obj.plot_power(
        dep_var="nobs", alpha=alpha, nobs=sample_sizes, effect_size=effect_sizes, alternative=alternative, ax=ax
    )

    return plt_fig


def calculate_t_test_statistic(prototype_samples, baseline_samples, alternative="less"):
    """Calculate the T-test result comparing the means of two independent samples (Prototype samples vs Baseline samples)

    This is a parametric test for normally distributed data.  It will be assumed that Prototype total time data will be normally distributed.
    In the event that total time data is not normally distributed, the Mann Whitney test should be used instead.

    This test is designed to be applied to data for one individual task, testing the following Null and Alternative Hypotheses.
    H0: The mean of Prototype distribution is the same or greater than the mean of Baseline distribution
    H1: The mean of Prototype distribution is the less than the mean of the Baseline distribution

    The above tests apply if we're testing (alternative='less'); if we're testing (alternative='greater') than
    H1 would be testing if the Prototype distribution is greater than the mean of the Baseline distribution

    Args:
        prototype_samples (list): list of Prototype samples (either a list of total times or task grades)
        baseline_samples (list): list of Baseline samples (either a list of total times or task grades)
        alternative (str): specifies whether whether we're testing if Prototype distribution means are less ('less') or
            greater ('greater') than Baseline distribution mean in the Alternative Hypothesis

    Returns:
        scipy.stats.TtestResult: a TtestResult object containing the statistic value and p-value
    """

    return ttest_ind(a=prototype_samples, b=baseline_samples, equal_var=False, alternative=alternative)


def calculate_mann_whitney_statistic(prototype_samples, baseline_samples, alternative="less"):
    """Calculate the Mann-Whitney test result comparing the means of two independent samples (Prototype samples vs Baseline samples)

    This is a non-parametric test for non-parametric data (that doesn't fit a known distribution). This will likely be
    applicable for the task grade data which likely will not fit a known distribution.

    This test is designed to be applied to data for one individual task, testing the following Null and Alternative Hypotheses.
    H0: The mean of Prototype distribution is the same or greater than the mean of Baseline distribution
    H1: The mean of Prototype distribution is the less than the mean of the Baseline distribution

    The above tests apply if we're testing (alternative='less'); if we're testing (alternative='greater') than
    H1 would be testing if the Prototype distribution is greater than the mean of the Baseline distribution

    Args:
        prototype_samples (list): list of Prototype samples (either a list of total times or task grades)
        baseline_samples (list): list of Baseline samples (either a list of total times or task grades)
        alternative (str): specifies whether whether we're testing if Prototype distribution means are less ('less') or
            greater ('greater') than Baseline distribution mean in the Alternative Hypothesis

    Returns:
        scipy.stats.MannwhitneyuResult: a MannwhitneyuResult object containing the statistic value and p-value
    """

    return mannwhitneyu(x=prototype_samples, y=baseline_samples, use_continuity=True, alternative=alternative)


def generate_bounded_normal_dist_samples(mean, std_dev, upper_bound, lower_bound, num_samples=30):
    """Randomly generate a set of data values corresponding to a bounded normal distribution

    "Bounded" in this case refers to normally distributed data that has min or max value.  For example, if we want to
    generate synthetic task grade scores, we'd want an upper bound value of 100% (since a participant can't score higher than 100)

    Args:
        mean (float): mean of normal distribution to generate samples from
        std_dev (float): standard deviation of normal distribution to generate samples from
        upper_bound (float): upper bound of sample distribution
        lower_bound (float): lower bound of sample distribution
        num_samples (int): _description_. Defaults to 30.

    Returns:
        list: a list of values sampled from the specified distribution
    """

    # upper/lower bounds are within 3 standard deviations of mean
    assert (mean - 3 * std_dev) <= upper_bound, "The value of (mean - 3 * std_dev) must be less than your upper bound!"
    assert (mean + 3 * std_dev) >= lower_bound, "The value of (mean + 3 * std_dev) must be greater than your lower bound"

    # sample from the normal distribution
    samples = np.random.normal(mean, std_dev, num_samples)

    # filter out values outside of bounds
    samples = [value for value in samples if value <= upper_bound and value >= lower_bound]

    # continuously sample values and filter out-of-bounds values until we have total number of samples
    while len(samples) < num_samples:
        # sample and filter out-of-bounds samples again
        additional_samples = np.random.normal(mean, std_dev, num_samples)
        additional_samples = [value for value in samples if value <= upper_bound and value >= lower_bound]

        # add additional samples (if we now have enough samples, grab enough to hit num_samples maximum)
        if len(additional_samples) > num_samples - len(samples):
            samples = samples + additional_samples[0 : num_samples - len(samples)]
        else:
            samples = samples + additional_samples

    # return final list of bounded normal distribution samples
    return samples
