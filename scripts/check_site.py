#!/usr/bin/env python3
"""Check a fresh Jekyll build and its source essay publishing metadata."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

try:
    from essay_metadata import Essay, load_essays, normalized_url
except ModuleNotFoundError as error:
    raise SystemExit("Install check dependencies first: python -m pip install -r scripts/requirements.txt") from error


class Page(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: list[str] = []
        self.references: list[str] = []
        self.links: list[dict[str, str | None]] = []
        self.essay_status: list[str] = []
        self.writing_entries: list[dict] = []
        self.entry_depth = 0
        self.times: list[str] = []
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
        classes = (attrs.get("class") or "").split()
        if tag == "article":
            if self.entry_depth:
                self.entry_depth += 1
            elif "writing-entry" in classes:
                self.entry_depth = 1
                self.writing_entries.append({"url": attrs.get("data-essay-url", ""), "status": attrs.get("data-essay-status", ""), "text": "", "links": []})
            if "chinese-essay" in classes:
                self.essay_status.append(attrs.get("data-essay-status") or "")
        if tag == "time" and attrs.get("datetime"):
            self.times.append(attrs["datetime"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs)
            if self.entry_depth:
                self.writing_entries[-1]["links"].append(attrs["href"])
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
        if tag == "article" and self.entry_depth:
            self.entry_depth -= 1
        if tag == "title":
            self.title_depth = False
        if tag == "script":
            self.json_ld_depth = False

    def handle_data(self, data: str) -> None:
        if self.entry_depth:
            self.writing_entries[-1]["text"] += data
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


def atom_date_matches(value: str | None, expected: datetime, date_only: bool) -> bool:
    """Compare only authored precision, while still requiring an Atom timestamp.

    Jekyll/Ruby on Windows can serialize YAML dates with a fixed local offset
    instead of the historical DST offset. A YYYY-MM-DD source specifies a day,
    so compare the emitted calendar day without imposing an invented instant.
    Explicit source timestamps retain strict instant comparisons.
    """
    if not value:
        raise ValueError("missing Atom timestamp")
    actual = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if actual.tzinfo is None:
        raise ValueError("Atom timestamps need an explicit timezone offset")
    return actual.date() == expected.date() if date_only else actual == expected


def check_essay_output(essays: list[Essay], pages: dict[Path, Page], feed: ElementTree.Element | None,
                       root: Path, hosts: set[str]) -> list[str]:
    """Compare generated pages against source, including ongoing public essays."""
    errors: list[str] = []
    public = sorted((essay for essay in essays if essay.public), key=lambda essay: essay.date, reverse=True)
    expected = {essay.url: essay for essay in public}
    hidden = {essay.url: essay for essay in essays if not essay.public}
    built_urls = {normalized_url(page_url(path, root)): page for path, page in pages.items()}
    for url, essay in hidden.items():
        target = local_target(url, "/", root, hosts)
        if target and target[0].exists():
            errors.append(f"{essay.source}: private or excluded draft appears in build at {url}")
        for path, page in pages.items():
            for reference in page.references:
                resolved = local_target(reference, page_url(path, root), root, hosts)
                if resolved and target and resolved[0] == target[0]:
                    errors.append(f"{path.relative_to(root)}: links to private draft {url}")

    index = built_urls.get("/personal-blogs/")
    if index is None:
        errors.append("Writing index is missing at /personal-blogs/")
    else:
        indexed = [normalized_url(entry["url"]) for entry in index.writing_entries]
        if Counter(indexed) != Counter(expected.keys()):
            errors.append(f"Writing index membership differs from public essays (expected {sorted(expected)}, found {indexed})")
        indexed_dates = [expected[url].date for url in indexed if url in expected]
        if indexed_dates != sorted(indexed_dates, reverse=True):
            errors.append("Writing index must list essays by publication date, newest first")
        for entry in index.writing_entries:
            essay = expected.get(normalized_url(entry["url"]))
            if essay is None:
                continue
            if entry["status"] != essay.status:
                errors.append(f"Writing index: incorrect publication status for {essay.url}")
            if essay.url not in {normalized_url(link) for link in entry["links"]}:
                errors.append(f"Writing index: missing article link for {essay.url}")
            for field in (essay.title, essay.description):
                if "".join(field.split()) not in "".join(entry["text"].split()):
                    errors.append(f"Writing index: missing title or description for {essay.url}")
            if essay.status == "writing" and "写作中" not in entry["text"]:
                errors.append(f"Writing index: missing visible writing status for {essay.url}")

    # Match template order for equal dates using the actual index order. Unequal
    # dates are independently checked above, and URLs must match the source set.
    ordered = public
    if index and Counter(normalized_url(entry["url"]) for entry in index.writing_entries) == Counter(expected.keys()):
        ordered = [expected[normalized_url(entry["url"])] for entry in index.writing_entries]
    for position, essay in enumerate(ordered):
        page = built_urls.get(essay.url)
        if page is None:
            errors.append(f"{essay.source}: public essay was not generated at {essay.url}")
            continue
        if page.essay_status != [essay.status]:
            errors.append(f"{essay.url}: essay status does not match source ({essay.status})")
        if not page.titles or essay.title not in page.titles[0]:
            errors.append(f"{essay.url}: document title does not match source")
        if page.description.strip() != essay.description:
            errors.append(f"{essay.url}: description does not match source")
        for relation, neighbor in (("prev", ordered[position + 1] if position + 1 < len(ordered) else None),
                                   ("next", ordered[position - 1] if position > 0 else None)):
            links = [normalized_url(link["href"]) for link in page.links if relation in (link.get("rel") or "").split()]
            wanted = [neighbor.url] if neighbor else []
            if links != wanted:
                errors.append(f"{essay.url}: rel={relation} should link to {wanted}, found {links}")
        displayed_dates = {value[:10] for value in page.times}
        if essay.date.date().isoformat() not in displayed_dates:
            errors.append(f"{essay.url}: publication date is not displayed")
        if essay.updated.date() != essay.date.date() and essay.updated.date().isoformat() not in displayed_dates:
            errors.append(f"{essay.url}: last_modified_at is not displayed")

    if feed is not None:
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        latest = sorted(public, key=lambda essay: (essay.updated, essay.url), reverse=True)[:10]
        entries = feed.findall("atom:entry", namespace)
        actual = [normalized_url(entry.findtext("atom:id", namespaces=namespace) or "") for entry in entries]
        if actual != [essay.url for essay in latest]:
            errors.append(f"feed.xml: expected the 10 most recently updated public essays, found {actual}")
        for entry in entries:
            url = normalized_url(entry.findtext("atom:id", namespaces=namespace) or "")
            essay = expected.get(url)
            if essay is None:
                errors.append(f"feed.xml: contains a private or unknown essay {url}")
                continue
            for field, wanted, date_precision in (("published", essay.date, essay.date_only),
                                                   ("updated", essay.updated, essay.updated_date_only)):
                try:
                    if not atom_date_matches(entry.findtext(f"atom:{field}", namespaces=namespace), wanted, date_precision):
                        errors.append(f"feed.xml: {url} {field} differs from source")
                except (ValueError, TypeError):
                    errors.append(f"feed.xml: {url} has an invalid {field} timestamp")
            for field, wanted in (("title", essay.title), ("summary", essay.description)):
                if entry.findtext(f"atom:{field}", namespaces=namespace) != wanted:
                    errors.append(f"feed.xml: {url} {field} differs from source")
        if latest:
            try:
                if not atom_date_matches(feed.findtext("atom:updated", namespaces=namespace), latest[0].updated, latest[0].updated_date_only):
                    errors.append("feed.xml: feed updated timestamp must match the newest article update")
            except (ValueError, TypeError):
                errors.append("feed.xml: invalid feed updated timestamp")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("_site-preview"))
    parser.add_argument("--site-url", default="https://chunyangzhang.com")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--source-only", action="store_true", help="Validate article metadata without building")
    args = parser.parse_args()
    essays, errors = load_essays(args.source.resolve())
    if args.source_only:
        if errors:
            print("Source checks failed:\n" + "\n".join(f"  - {error}" for error in errors))
            return 1
        print(f"PASS: {len(essays)} essay sources; metadata, unique permalinks, publication status, and update dates.")
        return 0
    root = args.directory.resolve()
    if not (root / "index.html").is_file():
        parser.error(f"No built index.html found in {root}; run Jekyll first.")
    hosts = {urlsplit(args.site_url).hostname or "chunyangzhang.com", "localhost", "127.0.0.1"}
    pages = {path: Page(path) for path in sorted(root.rglob("*.html"))}
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
    feed = None
    try:
        feed = ElementTree.parse(feed_path).getroot()
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        if feed.tag != "{http://www.w3.org/2005/Atom}feed":
            errors.append("feed.xml: expected an Atom feed")
        for field in ("title", "id", "updated"):
            if not (feed.findtext(f"atom:{field}", namespaces=namespace) or "").strip():
                errors.append(f"feed.xml: missing {field}")
        entries = feed.findall("atom:entry", namespace)
        if not entries and any(essay.public for essay in essays):
            errors.append("feed.xml: no published essay entries")
        entry_ids: list[str] = []
        for entry in entries:
            for field in ("title", "id", "published", "updated", "summary"):
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

    errors.extend(check_essay_output(essays, pages, feed, root, hosts))

    if errors:
        print("Build checks failed:")
        for error in sorted(set(errors)):
            print(f"  - {error}")
        return 1
    print(f"PASS: {len(pages)} HTML pages; {references} local HTML/CSS/feed references; {len(essays)} essay sources; metadata, index/feed membership, update dates, adjacent articles, drafts, headings, landmarks, assets, anchors, JSON-LD, and 404.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
