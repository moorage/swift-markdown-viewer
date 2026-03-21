#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path


def load_meta(case_dir: Path) -> dict[str, object]:
    return json.loads(case_dir.joinpath("meta.json").read_text(encoding="utf-8"))


def select_cases(case_dirs: list[Path], per_section: int, max_total: int) -> list[Path]:
    grouped: dict[str, list[Path]] = defaultdict(list)
    for case_dir in sorted(case_dirs):
        meta = load_meta(case_dir)
        section = str(meta.get("section", "unknown"))
        grouped[section].append(case_dir)

    selected: list[Path] = []
    for section in sorted(grouped):
        selected.extend(grouped[section][:per_section])
        if len(selected) >= max_total:
            return selected[:max_total]
    return selected[:max_total]


def copy_suite(source_suite: Path, destination_suite: Path, per_section: int, max_total: int) -> int:
    case_dirs = [path for path in source_suite.iterdir() if path.is_dir()]
    selected = select_cases(case_dirs, per_section=per_section, max_total=max_total)
    destination_suite.mkdir(parents=True, exist_ok=True)
    for case_dir in selected:
        shutil.copytree(case_dir, destination_suite / case_dir.name, dirs_exist_ok=True)
    return len(selected)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a smaller starter subset from spec fixtures.")
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    parser.add_argument("--per-section", type=int, default=2)
    parser.add_argument("--max-per-suite", type=int, default=80)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    destination_root = args.destination_root.resolve()
    shutil.rmtree(destination_root, ignore_errors=True)
    destination_root.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "sourceRoot": str(source_root),
        "perSection": args.per_section,
        "maxPerSuite": args.max_per_suite,
        "suites": {},
    }

    for suite in sorted(path for path in source_root.iterdir() if path.is_dir()):
        count = copy_suite(
            suite,
            destination_root / suite.name,
            per_section=args.per_section,
            max_total=args.max_per_suite,
        )
        manifest["suites"][suite.name] = {"selectedCount": count}

    destination_root.joinpath("manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(destination_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
