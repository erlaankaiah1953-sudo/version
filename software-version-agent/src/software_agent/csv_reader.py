import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RequiredSoftware:
    name: str
    required_version: str = ""


_NAME_KEYS = ("software", "name", "software_name", "package")
_VERSION_KEYS = ("required_version", "version", "min_version")


def _pick(row: dict, keys: tuple) -> str:
    for k in keys:
        if k in row and row[k] is not None:
            return row[k].strip()
    return ""


def read_required_software(path: str | Path) -> list[RequiredSoftware]:
    """Read the CSV. Header names are matched case-insensitively."""
    items: list[RequiredSoftware] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {(k or "").strip().lower(): v for k, v in raw.items()}
            name = _pick(row, _NAME_KEYS)
            if name:
                items.append(RequiredSoftware(name, _pick(row, _VERSION_KEYS)))
    return items
