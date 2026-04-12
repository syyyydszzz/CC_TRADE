#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

KIND_CONFIG = {
    "hypothesis": {"prefix": "h", "directory": "hypotheses"},
    "experiment": {"prefix": "e", "directory": "experiments"},
}


def generate_next_id(kind: str, repo_root: Path) -> str:
    config = KIND_CONFIG[kind]
    directory = repo_root / "research_log" / config["directory"]
    pattern = re.compile(rf"^{config['prefix']}(\d+)\.md$")

    max_seen = 0
    if directory.exists():
        for path in directory.iterdir():
            if not path.is_file():
                continue
            match = pattern.match(path.name)
            if match:
                max_seen = max(max_seen, int(match.group(1)))

    return f"{config['prefix']}{max_seen + 1:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the next hypothesis_id or experiment_id from research_log files."
    )
    parser.add_argument("kind", choices=("hypothesis", "experiment"))
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root containing research_log/. Defaults to the current directory.",
    )
    args = parser.parse_args()

    print(generate_next_id(args.kind, Path(args.root).resolve()))


if __name__ == "__main__":
    main()
