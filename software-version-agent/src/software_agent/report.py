import csv
from dataclasses import asdict, fields
from pathlib import Path

from .version_checker import VersionResult


def write_report(results: list[VersionResult], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[f.name for f in fields(VersionResult)])
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
    return path


def print_summary(results: list[VersionResult]) -> None:
    print(f"\n{'Software':<20}{'Required':<12}{'Latest':<14}Status")
    print("-" * 62)
    for r in results:
        print(f"{r.name:<20}{r.required_version:<12}{r.latest_version:<14}{r.status}")
