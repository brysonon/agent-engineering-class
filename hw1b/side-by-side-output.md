# Side-by-side: 1a plain text vs 1b structured output

Every run below uses `gpt-5.6-luna` and the same app, `structured_app.py`. Within each case the input file is identical; the only differences are which prompt file is passed and whether `--schema` is set. The 1a column is the prompt and plain-text output from homework 1a, reproduced here so the two can be compared directly.

Cost and elapsed time are from the app's own usage report. Single runs, so treat the timings as rough.

## Mixed signals (the 1a Avatar case)

**Input** (`bender-input-mixed.txt`):
````text
I am a waterbender, but I am free-spirited.
````

### 1a - plain text

````console
$ python structured_app.py bender-prompt-1a.md bender-input-mixed.txt --model gpt-5.6-luna
````

````text
Avatar
````

*2.7s, $0.000068*

### 1b - structured output

````console
$ python structured_app.py bender-prompt.md bender-input-mixed.txt --model gpt-5.6-luna --schema bender
````

````json
{
  "evidence": [
    {
      "quote": "I am a waterbender",
      "trait": "Explicitly identifies as a waterbender",
      "element": "Water"
    },
    {
      "quote": "free-spirited",
      "trait": "Free-spirited",
      "element": "Air"
    }
  ],
  "element": "Avatar",
  "confidence": "high"
}
````

*3.7s, $0.000236*

## Empty input (the 1a hallucination case)

**Input** (`bender-input-empty.txt`):
````text
(empty file)
````

### 1a - plain text

````console
$ python structured_app.py bender-prompt-1a.md bender-input-empty.txt --model gpt-5.6-luna
````

````text
Airbender
````

*4.43s, $0.000196*

### 1b - structured output

````console
$ python structured_app.py bender-prompt.md bender-input-empty.txt --model gpt-5.6-luna --schema bender
````

````json
{
  "evidence": [],
  "element": "Unknown",
  "confidence": "high"
}
````

*3.94s, $0.000168*

## Off-topic input

**Input** (`bender-input-offtopic.txt`):
````text
I like pizza and my favorite color is green.
````

### 1a - plain text

````console
$ python structured_app.py bender-prompt-1a.md bender-input-offtopic.txt --model gpt-5.6-luna
````

````text
Earthbender
````

*2.71s, $0.000084*

### 1b - structured output

````console
$ python structured_app.py bender-prompt.md bender-input-offtopic.txt --model gpt-5.6-luna --schema bender
````

````json
{
  "evidence": [],
  "element": "Unknown",
  "confidence": "high"
}
````

*2.71s, $0.000157*

## Clear single element

**Input** (`bender-input-clear.txt`):
````text
I am ambitious and proud, and I lose my temper the moment someone doubts me.
````

### 1a - plain text

````console
$ python structured_app.py bender-prompt-1a.md bender-input-clear.txt --model gpt-5.6-luna
````

````text
Firebender
````

*2.58s, $0.000048*

### 1b - structured output

````console
$ python structured_app.py bender-prompt.md bender-input-clear.txt --model gpt-5.6-luna --schema bender
````

````json
{
  "evidence": [
    {
      "quote": "ambitious",
      "trait": "Ambitious",
      "element": "Fire"
    },
    {
      "quote": "proud",
      "trait": "Proud",
      "element": "Fire"
    },
    {
      "quote": "I lose my temper",
      "trait": "Short-tempered",
      "element": "Fire"
    }
  ],
  "element": "Firebender",
  "confidence": "high"
}
````

*3.35s, $0.000280*

## Forbidden library requested (the 1a CANNOT COMPLY case)

**Input** (`code-input-numpy.txt`):
````text
Give me code that will generate the first 100 digits of pi. Use numpy matrices.
````

### 1a - plain text

````console
$ python structured_app.py code-prompt-1a.md code-input-numpy.txt --model gpt-5.6-luna
````

````text
CANNOT COMPLY: NumPy is a third-party library, but only the Python standard library is allowed.
````

*3.21s, $0.000141*

### 1b - structured output

````console
$ python structured_app.py code-prompt.md code-input-numpy.txt --model gpt-5.6-luna --schema code
````

````json
{
  "status": "cannot_comply",
  "reason": "The request explicitly requires NumPy matrices, but third-party imports are forbidden and NumPy is not part of the Python standard library.",
  "imports_used": [],
  "code": null,
  "assumptions": []
}
````

*2.97s, $0.000176*

## Satisfiable request

**Input** (`code-input-valid.txt`):
````text
Give me code that will generate the first 100 digits of pi.
````

### 1a - plain text

````console
$ python structured_app.py code-prompt-1a.md code-input-valid.txt --model gpt-5.6-luna
````

````text
```python
from decimal import Decimal, localcontext


def generate_first_100_digits() -> str:
    """Calculate and return the first 100 digits of pi, without a decimal point."""
    # We keep some extra digits so our answer has room to be careful.
    digit_count = 100
    extra_digits = 20

    # Chudnovsky's recipe lets us make pi very quickly.
    with localcontext() as context:
        context.prec = digit_count + extra_digits

        # These are the starting numbers in the recipe.
        middle_sum = Decimal(13_591_409)
        multiplier = 1
        x_value = 1
        k_value = 6

        # Each loop adds about 14 more correct digits.
        term_count = digit_count // 14 + 2
        for index in range(1, term_count):
            # This makes the next part of the big recipe.
            multiplier *= (k_value**3 - 16 * k_value)
            multiplier //= index**3

            x_value *= -262_537_412_640_768_000
            middle_sum += (
                Decimal(multiplier * (13_591_409 + 5_451_401_34 * index))
                / Decimal(x_value)
            )

            k_value += 12

        # This final step turns the recipe's answer into pi.
        pi_value = Decimal(426_880) * Decimal(10_005).sqrt() / middle_sum

        # Make a long text answer, then keep only the first 100 digits.
        pi_text = format(pi_value, f".{digit_count + extra_digits}f")
        return pi_text.replace(".", "")[:digit_count]


if __name__ == "__main__":
    print(generate_first_100_digits())
```
````

Extracted from the fenced block, after stripping the Markdown fence:

````python
from decimal import Decimal, localcontext


def generate_first_100_digits() -> str:
    """Calculate and return the first 100 digits of pi, without a decimal point."""
    # We keep some extra digits so our answer has room to be careful.
    digit_count = 100
    extra_digits = 20

    # Chudnovsky's recipe lets us make pi very quickly.
    with localcontext() as context:
        context.prec = digit_count + extra_digits

        # These are the starting numbers in the recipe.
        middle_sum = Decimal(13_591_409)
        multiplier = 1
        x_value = 1
        k_value = 6

        # Each loop adds about 14 more correct digits.
        term_count = digit_count // 14 + 2
        for index in range(1, term_count):
            # This makes the next part of the big recipe.
            multiplier *= (k_value**3 - 16 * k_value)
            multiplier //= index**3

            x_value *= -262_537_412_640_768_000
            middle_sum += (
                Decimal(multiplier * (13_591_409 + 5_451_401_34 * index))
                / Decimal(x_value)
            )

            k_value += 12

        # This final step turns the recipe's answer into pi.
        pi_value = Decimal(426_880) * Decimal(10_005).sqrt() / middle_sum

        # Make a long text answer, then keep only the first 100 digits.
        pi_text = format(pi_value, f".{digit_count + extra_digits}f")
        return pi_text.replace(".", "")[:digit_count]


if __name__ == "__main__":
    print(generate_first_100_digits())
````

Result: parses as valid Python.

*17.01s, $0.001538*

### 1b - structured output

````console
$ python structured_app.py code-prompt.md code-input-valid.txt --model gpt-5.6-luna --schema code
````

````json
{
  "status": "ok",
  "reason": null,
  "imports_used": [
    "decimal"
  ],
  "code": "# This brings in a very careful number box for doing the pi math.\nfrom decimal import Decimal, localcontext\n\n\n# This function makes a string with the requested number of important pi digits.\ndef generate_pi_digits(digits: int) -> str:\n    \"\"\"Return pi with the requested number of significant digits.\"\"\"\n    if digits < 1:\n        raise ValueError(\"digits must be at least 1\")\n\n    # This gives the number box some extra room so the answer stays accurate.\n    with localcontext() as context:\n        context.prec = digits + 25\n\n        # These are the starting numbers for a fast pi recipe.\n        total = Decimal(13591409)\n        term = Decimal(1)\n        terms = digits // 14 + 3\n\n        # Each loop adds one tiny piece of the pi recipe.\n        for k in range(1, terms):\n            numerator = 1\n            for value in range(6 * k - 5, 6 * k + 1):\n                numerator *= value\n            denominator = (\n                (3 * k - 2)\n                * (3 * k - 1)\n                * (3 * k)\n                * k**3\n                * 640320**3\n            )\n            term *= Decimal(-numerator) / Decimal(denominator)\n            total += term * Decimal(13591409 + 545140134 * k)\n\n        # This finishes the recipe and turns the answer into ordinary text.\n        pi = Decimal(426880) * Decimal(10005).sqrt() / total\n        text = format(pi, f\".{digits + 20}f\")\n        return text[: digits + 1]\n\n\n# This little example prints the first 100 significant digits of pi.\nif __name__ == '__main__':\n    print(generate_pi_digits(100))\n",
  "assumptions": [
    "The first 100 digits means 100 significant digits, including the leading 3; the decimal point is displayed but is not counted."
  ]
}
````

Extracted from the `code` field, unescaped:

````python
# This brings in a very careful number box for doing the pi math.
from decimal import Decimal, localcontext


# This function makes a string with the requested number of important pi digits.
def generate_pi_digits(digits: int) -> str:
    """Return pi with the requested number of significant digits."""
    if digits < 1:
        raise ValueError("digits must be at least 1")

    # This gives the number box some extra room so the answer stays accurate.
    with localcontext() as context:
        context.prec = digits + 25

        # These are the starting numbers for a fast pi recipe.
        total = Decimal(13591409)
        term = Decimal(1)
        terms = digits // 14 + 3

        # Each loop adds one tiny piece of the pi recipe.
        for k in range(1, terms):
            numerator = 1
            for value in range(6 * k - 5, 6 * k + 1):
                numerator *= value
            denominator = (
                (3 * k - 2)
                * (3 * k - 1)
                * (3 * k)
                * k**3
                * 640320**3
            )
            term *= Decimal(-numerator) / Decimal(denominator)
            total += term * Decimal(13591409 + 545140134 * k)

        # This finishes the recipe and turns the answer into ordinary text.
        pi = Decimal(426880) * Decimal(10005).sqrt() / total
        text = format(pi, f".{digits + 20}f")
        return text[: digits + 1]


# This little example prints the first 100 significant digits of pi.
if __name__ == '__main__':
    print(generate_pi_digits(100))
````

Result: parses as valid Python.

*18.1s, $0.001897*
