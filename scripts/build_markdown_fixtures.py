#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_VIEWPORT = {
    "platforms": {
        "iphone": {"width": 390, "height": 844, "scale": 3},
        "ipad": {"width": 820, "height": 1180, "scale": 2},
        "mac": {"width": 1280, "height": 900, "scale": 2},
    },
    "initial_scroll_y": 0,
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "untitled"


def safe_get_str(obj: dict[str, Any], key: str, default: str = "") -> str:
    value = obj.get(key, default)
    return value if isinstance(value, str) else default


def safe_get_int(obj: dict[str, Any], key: str, default: int = 0) -> int:
    value = obj.get(key, default)
    return value if isinstance(value, int) else default


def write_case(out_root: Path, suite_name: str, index: int, case: dict[str, Any]) -> None:
    markdown = safe_get_str(case, "markdown")
    html = safe_get_str(case, "html")
    section = safe_get_str(case, "section", "unknown-section")
    example = safe_get_int(case, "example", index)
    start_line = safe_get_int(case, "start_line", 0)
    end_line = safe_get_int(case, "end_line", 0)

    section_slug = slugify(section)
    dirname = f"{index:04d}-{section_slug}-example-{example}"
    case_dir = out_root / suite_name / dirname
    case_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "input.md").write_text(markdown, encoding="utf-8")
    (case_dir / "expected.html").write_text(html, encoding="utf-8")
    (case_dir / "viewport.json").write_text(
        json.dumps(DEFAULT_VIEWPORT, indent=2) + "\n",
        encoding="utf-8",
    )
    (case_dir / "meta.json").write_text(
        json.dumps(
            {
                "suite": suite_name,
                "example": example,
                "section": section,
                "start_line": start_line,
                "end_line": end_line,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_suite(input_json: Path, out_root: Path, suite_name: str) -> int:
    cases = json.loads(input_json.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError(f"{input_json} did not contain a JSON list")

    written = 0
    for i, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            continue
        if "markdown" not in case or "html" not in case:
            continue
        write_case(out_root=out_root, suite_name=suite_name, index=i, case=case)
        written += 1
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "Usage: build_markdown_fixtures.py "
            "<commonmark-tests.json> <gfm-tests.json> <output-dir>",
            file=sys.stderr,
        )
        return 2

    commonmark_json = Path(argv[1]).resolve()
    gfm_json = Path(argv[2]).resolve()
    output_dir = Path(argv[3]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    commonmark_count = build_suite(commonmark_json, output_dir, "commonmark")
    gfm_count = build_suite(gfm_json, output_dir, "gfm")

    print(f"Wrote fixtures to {output_dir}")
    print(f"CommonMark cases: {commonmark_count}")
    print(f"GFM cases: {gfm_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
