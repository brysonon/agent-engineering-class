# Structured output: does field order change accuracy?

Model: `gpt-5.6-luna`. 10 problems x 3 trials = 30 calls per cell.

| Reasoning effort | Field order | Accuracy | Median time (s) | `reasoning` field (chars) | Internal reasoning tokens | Cost (USD) |
|------------------|-------------|----------|-----------------|---------------------------|---------------------------|------------|
| none | reasoning-first | 27/30 = 90.0% | 1.88 | 147 | 0 | $0.0035 |
| none | answer-first | 26/30 = 86.7% | 1.83 | 151 | 0 | $0.0036 |
| high | reasoning-first | 29/30 = 96.7% | 2.27 | 161 | 53 | $0.0054 |
| high | answer-first | 29/30 = 96.7% | 2.21 | 160 | 49 | $0.0057 |

## Per-problem accuracy

### effort = high

| Problem | Expected | reasoning-first | answer-first |
|---------|----------|-----------------|--------------|
| yolanda-bob | 24 | 3/3 | 3/3 |
| avg-speed | 52.5 | 3/3 | 2/3 |
| markup-discount | 5 | 3/3 | 3/3 |
| machines | 3 | 3/3 | 3/3 |
| bat-ball | 0.05 | 3/3 | 3/3 |
| div-3-or-5 | 2418 | 3/3 | 3/3 |
| pipes | 5.14286 | 2/3 | 3/3 |
| average-removed | 12 | 3/3 | 3/3 |
| compound-interest | 1331 | 3/3 | 3/3 |
| distinct-digits | 648 | 3/3 | 3/3 |

### effort = none

| Problem | Expected | reasoning-first | answer-first |
|---------|----------|-----------------|--------------|
| yolanda-bob | 24 | 3/3 | 2/3 |
| avg-speed | 52.5 | 3/3 | 3/3 |
| markup-discount | 5 | 3/3 | 3/3 |
| machines | 3 | 3/3 | 3/3 |
| bat-ball | 0.05 | 3/3 | 3/3 |
| div-3-or-5 | 2418 | 2/3 | 3/3 |
| pipes | 5.14286 | 1/3 | 0/3 |
| average-removed | 12 | 3/3 | 3/3 |
| compound-interest | 1331 | 3/3 | 3/3 |
| distinct-digits | 648 | 3/3 | 3/3 |
