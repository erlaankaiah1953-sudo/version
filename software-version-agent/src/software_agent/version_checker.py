import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from google import genai
from google.genai import types
from packaging.version import InvalidVersion, Version

from .csv_reader import RequiredSoftware

SYSTEM_PROMPT = """You find the latest stable release version of software.
Use Google Search, preferring official sources (project site, release page, GitHub releases).
Ignore betas, release candidates and nightly builds.
Reply with ONLY a JSON object, no markdown fences, in this form:
{"latest_version": "x.y.z", "source": "https://...", "release_date": "YYYY-MM-DD or empty"}
If you cannot determine it, use "latest_version": "unknown"."""


@dataclass
class VersionResult:
    name: str
    required_version: str
    latest_version: str
    status: str
    source: str
    release_date: str
    checked_at: str


def _parse(v: str) -> Version | None:
    try:
        return Version(re.sub(r"^[vV]", "", v.strip()))
    except InvalidVersion:
        return None


def compare(required: str, latest: str) -> str:
    if latest in ("", "unknown"):
        return "UNKNOWN"
    if not required:
        return "NO_REQUIREMENT"
    req, lat = _parse(required), _parse(latest)
    if req is None or lat is None:
        return "UNKNOWN"
    # Compare only as deep as the requirement is specified (e.g. "3.12" vs "3.12.7")
    depth = len(req.release)
    lat_trim = lat.release[:depth]
    if lat_trim == req.release:
        return "UP_TO_DATE"
    return "OUTDATED" if lat_trim > req.release else "AHEAD_OF_LATEST"


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in response: {text[:200]}")
    return json.loads(match.group(0))


class VersionChecker:
    def __init__(self) -> None:
        # Reads GEMINI_API_KEY (or GOOGLE_API_KEY) from the environment
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = os.getenv("MODEL", "gemini-2.5-flash")
        # Google Search grounding gives the model live web results.
        # (JSON response mode can't be combined with search, so we parse the text.)
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0,
        )

    def _ask(self, name: str) -> dict:
        resp = self.client.models.generate_content(
            model=self.model,
            contents=f"What is the latest stable version of {name}?",
            config=self.config,
        )
        return _extract_json(resp.text or "")

    def check(self, item: RequiredSoftware) -> VersionResult:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            data = self._ask(item.name)
            latest = str(data.get("latest_version", "unknown")).strip()
            return VersionResult(
                item.name, item.required_version, latest,
                compare(item.required_version, latest),
                data.get("source", ""), data.get("release_date", ""), now,
            )
        except Exception as e:  # keep going if one lookup fails
            return VersionResult(
                item.name, item.required_version, "unknown",
                f"ERROR: {e}"[:120], "", "", now,
            )
