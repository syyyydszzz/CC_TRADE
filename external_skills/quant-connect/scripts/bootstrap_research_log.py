#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the research_log directory structure used by the quant-connect skill."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root where research_log/ should be created. Defaults to the current directory.",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    research_log = repo_root / "research_log"
    ensure_directory(research_log / "hypotheses")
    ensure_directory(research_log / "experiments")

    print(f"Initialized research log at {research_log}")


if __name__ == "__main__":
    main()
