from __future__ import annotations

import argparse

from .synth import write_input_json


def main() -> None:
    parser = argparse.ArgumentParser(prog="pgx-fhir")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Generate a synthetic PGx input JSON")
    demo.add_argument("out", help="Output path, e.g. examples/input.example.json")
    demo.add_argument("--seed", type=int, default=7)

    args = parser.parse_args()

    if args.cmd == "demo":
        path = write_input_json(args.out, seed=args.seed)
        print(str(path))


if __name__ == "__main__":
    main()
