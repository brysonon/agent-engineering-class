#!/usr/bin/env python3
"""Print the type of each top-level value in a TOML configuration file."""

import argparse
import tomllib


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="path to a TOML file")
    args = parser.parse_args()

    with open(args.path, "rb") as toml_file:
        config = tomllib.load(toml_file)

    for key, value in config.items():
        print(f"{key}: {type(value).__name__}")


if __name__ == "__main__":
    main()
