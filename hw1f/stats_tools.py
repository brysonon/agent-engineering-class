import random
import statistics
from math import exp, lgamma, log

from tools import ToolBox

toolbox = ToolBox()


@toolbox.tool
def random_integer(low: int, high: int, count: int) -> str:
    """Returns `count` truly random integers between low and high (inclusive), comma-separated."""
    return ', '.join(str(random.randint(low, high)) for _ in range(count))


@toolbox.tool
def binomial_probability(n: int, k: int, p: float) -> float:
    """Exact probability of exactly k successes in n independent trials with success probability p."""
    if p in (0, 1):
        return float(k == n * p)
    # Work in log space so huge n (e.g. 10,000 flips) doesn't overflow a float
    log_comb = lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
    return exp(log_comb + k * log(p) + (n - k) * log(1 - p))


@toolbox.tool
def normal_probability(mean: float, std_dev: float, x: float) -> float:
    """Probability that a normally distributed value is less than or equal to x (the CDF)."""
    return statistics.NormalDist(mean, std_dev).cdf(x)


@toolbox.tool
def describe_numbers(numbers: str) -> str:
    """Mean, median, sample standard deviation, min, and max of a comma-separated list of numbers."""
    values = [float(v) for v in numbers.split(',')]
    return (
        f'count={len(values)}, mean={statistics.mean(values)}, median={statistics.median(values)}, '
        f'stdev={statistics.stdev(values) if len(values) > 1 else 0}, min={min(values)}, max={max(values)}'
    )
