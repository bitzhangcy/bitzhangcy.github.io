"""Read the essay publishing contract shared by the site checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from fnmatch import fnmatchcase
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """A typo should not silently replace another front-matter field."""


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML field {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def yaml_mapping(text: str) -> dict:
    value = yaml.load(text, Loader=UniqueKeyLoader)
    if not isinstance(value, dict):
        raise ValueError("expected a YAML mapping")
    return value


def front_matter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML front matter")
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise ValueError("front matter has no closing ---")
    return yaml_mapping("\n".join(lines[1:end]))


def timestamp(value: object, timezone: ZoneInfo) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time.min)
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError("expected an ISO date (YYYY-MM-DD) or timestamp")
    return result if result.tzinfo else result.replace(tzinfo=timezone)


def date_only(value: object) -> bool:
    """Retain the precision authored in YAML, including quoted ISO dates."""
    return ((isinstance(value, date) and not isinstance(value, datetime))
            or (isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()) is not None))


def normalized_url(value: str) -> str:
    path = unquote(urlsplit(value).path)
    return path[:-10] if path.endswith("/index.html") else path


def path_matches(path: str, scope: str) -> bool:
    scope = scope.strip("/")
    return not scope or path == scope or path.startswith(scope + "/") or fnmatchcase(path, scope)


@dataclass(frozen=True)
class Essay:
    source: str
    url: str
    title: str
    description: str
    date: datetime
    updated: datetime
    status: str
    public: bool
    date_only: bool
    updated_date_only: bool


def load_essays(source: Path) -> tuple[list[Essay], list[str]]:
    errors: list[str] = []
    try:
        config = yaml_mapping((source / "_config.yml").read_text(encoding="utf-8-sig"))
        timezone = ZoneInfo(config.get("timezone", "UTC"))
    except (OSError, ValueError, KeyError, yaml.YAMLError) as error:
        return [], [f"_config.yml: {error}"]

    defaults = sorted(config.get("defaults", []), key=lambda item: len(item.get("scope", {}).get("path", "")))
    essays: list[Essay] = []
    seen_urls: dict[str, str] = {}
    for path in sorted((source / "blogs").rglob("*")):
        if path.suffix.lower() not in {".md", ".markdown", ".html"}:
            continue
        relative = path.relative_to(source).as_posix()
        try:
            values = {}
            for item in defaults:
                scope = item.get("scope", {})
                if scope.get("type", "pages") in {"", "pages"} and path_matches(relative, scope.get("path", "")):
                    values.update(item.get("values", {}))
            values.update(front_matter(path))
        except (OSError, ValueError, TypeError, yaml.YAMLError) as error:
            errors.append(f"{relative}: {error}")
            continue

        start_errors = len(errors)
        excluded = any(path_matches(relative, str(pattern)) for pattern in config.get("exclude", []))
        published = values.get("published", True)
        if not isinstance(published, bool):
            errors.append(f"{relative}: published must be true or false, without quotes")
        public = published is not False and not excluded
        if values.get("layout") != "essay":
            errors.append(f"{relative}: layout must resolve to essay (check front matter and defaults)")
        for field in ("title", "description"):
            value = values.get(field)
            if not isinstance(value, str) or (not value.strip() and (public or field == "title")):
                errors.append(f"{relative}: {field} must be a nonempty string" if public or field == "title" else f"{relative}: description must be a string")
        status = values.get("status", "complete")
        if not isinstance(status, str) or status not in {"writing", "complete"}:
            errors.append(f"{relative}: status must be writing or complete")

        permalink = values.get("permalink")
        if not isinstance(permalink, str):
            errors.append(f"{relative}: missing permalink")
        else:
            parsed = urlsplit(permalink)
            decoded = unquote(parsed.path)
            if (not permalink.startswith("/blogs/") or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
                    or any(part in {".", ".."} for part in decoded.split("/"))
                    or any(character.isspace() for character in permalink) or "\\" in decoded
                    or not (permalink.endswith("/") or permalink.endswith(".html"))):
                errors.append(f"{relative}: permalink must be a local /blogs/.../ or /blogs/....html URL")
            canonical = normalized_url(permalink)
            if canonical in seen_urls:
                errors.append(f"{relative}: duplicate permalink {permalink} (also {seen_urls[canonical]})")
            seen_urls[canonical] = relative
        try:
            published_at = timestamp(values.get("date"), timezone)
            updated_at = timestamp(values.get("last_modified_at", values.get("date")), timezone)
            if updated_at < published_at:
                errors.append(f"{relative}: last_modified_at must not be earlier than date")
        except (ValueError, TypeError) as error:
            errors.append(f"{relative}: invalid date or last_modified_at: {error}")
        if len(errors) == start_errors:
            essays.append(Essay(relative, normalized_url(permalink), values["title"].strip(), values["description"].strip(), published_at, updated_at, status, public,
                                date_only(values["date"]), date_only(values.get("last_modified_at", values["date"]))))
    return essays, errors
