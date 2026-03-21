#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        if source.is_file():
            shutil.copy2(source, destination)
        else:
            shutil.copytree(source, destination, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge Safari reference captures into a repo-local golden layout.")
    parser.add_argument("source_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    destination_root = args.destination_root.resolve()
    destination_root.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "sourceRoot": str(source_root),
        "destinationRoot": str(destination_root),
        "entries": [],
    }

    for metadata_path in sorted(source_root.rglob("metadata.json")):
        capture_dir = metadata_path.parent
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        fixture_dir = Path(metadata["fixtureDir"]).resolve()
        suite = fixture_dir.parent.name
        case = fixture_dir.name
        destination_dir = destination_root / suite / case
        destination_dir.mkdir(parents=True, exist_ok=True)

        copy_if_exists(capture_dir / "safari-window.png", destination_dir / "reference-safari.png")
        copy_if_exists(capture_dir / "metadata.json", destination_dir / "reference-safari-metadata.json")
        copy_if_exists(capture_dir / "reference.html", destination_dir / "reference.html")
        copy_if_exists(capture_dir / "expected.html", destination_dir / "expected.html")
        copy_if_exists(capture_dir / "viewport.json", destination_dir / "viewport.json")
        copy_if_exists(capture_dir / "meta.json", destination_dir / "meta.json")
        copy_if_exists(capture_dir / "input.md", destination_dir / "input.md")

        manifest["entries"].append(
            {
                "suite": suite,
                "case": case,
                "captureDir": str(capture_dir),
                "goldenDir": str(destination_dir),
                "browser": metadata.get("browser"),
                "browserVersion": metadata.get("browserVersion"),
                "deviceClass": metadata.get("deviceClass"),
            }
        )

    destination_root.joinpath("manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(destination_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
