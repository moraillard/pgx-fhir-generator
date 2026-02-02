from __future__ import annotations

import argparse
import json
from pathlib import Path

from .fhir import build_bundle_from_pgx_input
from .models import PgXInput
from .synth import write_input_json


def main() -> None:
    parser = argparse.ArgumentParser(prog="pgx-fhir")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Generate a synthetic PGx input JSON")
    demo.add_argument("out", help="Output path, e.g. examples/input.example.json")
    demo.add_argument("--seed", type=int, default=7)

    bundle = sub.add_parser("bundle", help="Build a minimal FHIR Bundle from a PGx input JSON")
    bundle.add_argument("infile", help="Input PGx JSON, e.g. examples/input.example.json")
    bundle.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()

    if args.cmd == "demo":
        path = write_input_json(args.out, seed=args.seed)
        print(str(path))
        return

    if args.cmd == "bundle":
        data = Path(args.infile).read_text(encoding="utf-8")
        pgx_input = PgXInput.model_validate_json(data)
        bundle_json = build_bundle_from_pgx_input(pgx_input)

        if args.pretty:
            print(json.dumps(bundle_json, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(bundle_json, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
