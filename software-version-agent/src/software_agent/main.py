import os
import sys

from dotenv import load_dotenv

from .csv_reader import read_required_software
from .report import print_summary, write_report
from .version_checker import VersionChecker


def main() -> None:
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")

    input_csv = os.getenv("INPUT_CSV", "requiredsoftwares.csv")
    output_csv = os.getenv("OUTPUT_CSV", "reports/latest_versions.csv")

    items = read_required_software(input_csv)
    if not items:
        sys.exit(f"No software entries found in {input_csv}")

    checker = VersionChecker()
    results = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Checking {item.name}...")
        results.append(checker.check(item))

    path = write_report(results, output_csv)
    print_summary(results)
    print(f"\nReport written to {path}")


if __name__ == "__main__":
    main()
