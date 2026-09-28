import random
import statistics
from math import comb

from tools import ToolBox

toolbox = ToolBox()


@toolbox.tool
def random_integer(low: int, high: int, count: int) -> str:
    """Returns `count` truly random integers between low and high (inclusive), comma-separated."""
    return ', '.join(str(random.randint(low, high)) for _ in range(count))


@toolbox.tool
def binomial_probability(n: int, k: int, p: float) -> float:
    """Exact probability of exactly k successes in n independent trials with success probability p."""
    return comb(n, k) * p ** k * (1 - p) ** (n - k)


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
