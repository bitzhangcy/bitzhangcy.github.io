#!/usr/bin/env python3
"""Check a fresh Jekyll build without third-party Python dependencies."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree


class Page(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: list[str] = []
        self.references: list[str] = []
        self.headings = 0
        self.main_count = 0
        self.titles: list[str] = []
        self.title_depth = False
        self.description = ""
        self.canonicals: list[str] = []
        self.image_alt_missing = 0
        self.lang = ""
        self.json_ld: list[str] = []
        self.json_ld_depth = False
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.append(attrs["name"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.references.append(attrs[key])
        if tag == "h1":
            self.headings += 1
        if tag == "main" or attrs.get("role") == "main":
            self.main_count += 1
        if tag == "title":
            self.titles.append("")
            self.title_depth = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content") or ""
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href") or "")
        if tag == "img" and "alt" not in attrs:
            self.image_alt_missing += 1
        if tag == "html":
            self.lang = attrs.get("lang") or ""
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.json_ld.append("")
            self.json_ld_depth = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title_depth = False
        if tag == "script":
            self.json_ld_depth = False

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.titles[-1] += data
        if self.json_ld_depth:
            self.json_ld[-1] += data


def page_url(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    return "/" + (relative[:-10] if relative.endswith("index.html") else relative)


def local_target(reference: str, current_url: str, root: Path, hosts: set[str]) -> tuple[Path, str] | None:
    parsed = urlsplit(urljoin("https://" + sorted(hosts)[0] + current_url, reference))
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in hosts:
        return None
    target = (root / unquote(parsed.path).lstrip("/")).resolve()
    if not target.is_relative_to(root):
        return target, unquote(parsed.fragment)
    if target.is_dir():
        target = target / "index.html"
    elif not target.exists() and not target.suffix:
        target = target / "index.html"
    return target, unquote(parsed.fragment)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("_site-preview"))
    parser.add_argument("--site-url", default="https://chunyangzhang.com")
    args = parser.parse_args()
    root = args.directory.resolve()
    if not (root / "index.html").is_file():
        parser.error(f"No built index.html found in {root}; run Jekyll first.")
    hosts = {urlsplit(args.site_url).hostname or "chunyangzhang.com", "localhost", "127.0.0.1"}
    pages = {path: Page(path) for path in sorted(root.rglob("*.html"))}
    errors: list[str] = []
    references = 0

    def check_reference(reference: str, current_url: str, label: str) -> None:
        nonlocal references
        target = local_target(reference, current_url, root, hosts)
        if target is None:
            return
        references += 1
        path, fragment = target
        if not path.is_relative_to(root) or not path.is_file():
            errors.append(f"{label}: missing local target {reference}")
        elif fragment and path in pages and fragment not in pages[path].ids:
            errors.append(f"{label}: missing anchor {reference}")

    for path, page in pages.items():
        label = path.relative_to(root).as_posix()
        if len(page.titles) != 1 or not page.titles[0].strip():
            errors.append(f"{label}: expected one nonempty document title")
        if not page.description.strip():
            errors.append(f"{label}: missing page description")
        if len(page.canonicals) != 1 or not page.canonicals[0]:
            errors.append(f"{label}: expected one canonical URL")
        if page.headings != 1:
            errors.append(f"{label}: expected one h1, found {page.headings}")
        if page.main_count != 1:
            errors.append(f"{label}: expected one main landmark, found {page.main_count}")
        if not page.lang:
            errors.append(f"{label}: missing document language")
        if page.image_alt_missing:
            errors.append(f"{label}: {page.image_alt_missing} image(s) missing an alt attribute")
        for structured_data in page.json_ld:
            try:
                json.loads(structured_data)
            except json.JSONDecodeError as error:
                errors.append(f"{label}: invalid JSON-LD: {error}")
        for identifier, count in Counter(page.ids).items():
            if count > 1:
                errors.append(f"{label}: duplicate id {identifier!r}")
        for reference in page.references:
            check_reference(reference, page_url(path, root), label)

    for path in sorted(root.rglob("*.css")):
        label = path.relative_to(root).as_posix()
        for reference in re.findall(r"url\(\s*['\"]?([^'\"\s)]+)", path.read_text(encoding="utf-8")):
            check_reference(reference, "/" + label, label)

    if not (root / "404.html").is_file():
        errors.append("404.html: GitHub Pages requires this file at the site root")
    if not pages[root / "index.html"].json_ld:
        errors.append("index.html: missing structured identity data")

    feed_path = root / "feed.xml"
    try:
        feed = ElementTree.parse(feed_path).getroot()
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        if feed.tag != "{http://www.w3.org/2005/Atom}feed":
            errors.append("feed.xml: expected an Atom feed")
        for field in ("title", "id", "updated"):
            if not (feed.findtext(f"atom:{field}", namespaces=namespace) or "").strip():
                errors.append(f"feed.xml: missing {field}")
        entries = feed.findall("atom:entry", namespace)
        if not entries:
            errors.append("feed.xml: no published essay entries")
        entry_ids: list[str] = []
        for entry in entries:
            for field in ("title", "id", "updated", "summary"):
                if not (entry.findtext(f"atom:{field}", namespaces=namespace) or "").strip():
                    errors.append(f"feed.xml: an entry is missing {field}")
            entry_ids.append(entry.findtext("atom:id", namespaces=namespace) or "")
        if len(set(entry_ids)) != len(entry_ids):
            errors.append("feed.xml: duplicate entry ids")
        for link in feed.findall(".//atom:link", namespace):
            check_reference(link.get("href", ""), "/feed.xml", "feed.xml")
    except (OSError, ElementTree.ParseError) as error:
        errors.append(f"feed.xml: cannot read valid XML: {error}")

    for private_path in (".tools", "scripts", "vendor", "Gemfile", "Gemfile.lock", "README.md"):
        if (root / private_path).exists():
            errors.append(f"Unexpected development or draft content in build: {private_path}")

    # Check the configured local essay exclusions, so publishing a finished draft
    # later only requires the normal _config.yml change, not a checker edit.
    source = Path(__file__).resolve().parent.parent
    configuration = (source / "_config.yml").read_text(encoding="utf-8")
    excluded_essays = re.findall(r"(?m)^\s+-\s+(blogs/[^\s#]+\.md)\s*(?:#.*)?$", configuration)
    for excluded in excluded_essays:
        draft = source / excluded
        if not draft.is_file():
            continue
        draft_text = draft.read_text(encoding="utf-8")
        front_matter = draft_text.split("---", 2)[1] if draft_text.startswith("---") else ""
        permalink = re.search(r"(?m)^permalink:\s*['\"]?([^'\"\s]+)", front_matter)
        if permalink:
            target = local_target(permalink.group(1), "/", root, hosts)
            if target and target[0].exists():
                errors.append(f"Excluded draft appears in build: {excluded}")

    if errors:
        print("Build checks failed:")
        for error in sorted(set(errors)):
            print(f"  - {error}")
        return 1
    print(f"PASS: {len(pages)} HTML pages; {references} local HTML/CSS/feed references; metadata, headings, landmarks, assets, anchors, JSON-LD, Atom feed, 404, and build exclusions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
