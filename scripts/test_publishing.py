"""Regression checks for visibility, update ordering, and safe draft creation."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree

from check_site import Page, check_essay_output
from essay_metadata import load_essays
from new_essay import create_essay


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name)
        (self.source / "blogs").mkdir()
        (self.source / "_config.yml").write_text("""timezone: UTC
defaults:
  - scope:
      path: blogs
      type: pages
    values:
      layout: essay
      status: complete
""", encoding="utf-8")
        self.write_essay("old", "2020-01-01", "last_modified_at: 2026-09-16\n")
        self.write_essay("ongoing", "2026-09-01", "status: writing\n")
        self.write_essay("draft", "2026-09-15", "published: false\nstatus: writing\n")
        self.build = self.source / "output"
        self.build.mkdir()
        self.write_output()

    def write_essay(self, slug, published_date, extra=""):
        (self.source / "blogs" / f"{slug}.md").write_text(
            f"---\ntitle: {slug}\ndescription: About {slug}\npermalink: /blogs/{slug}/\ndate: {published_date}\n{extra}---\n\n## Section\n",
            encoding="utf-8")

    def write_html(self, url, html):
        path = self.build / url.strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return path

    def write_output(self):
        self.index_path = self.write_html("personal-blogs", """
<article class="writing-entry" data-essay-url="/blogs/ongoing/" data-essay-status="writing"><a href="/blogs/ongoing/">ongoing</a> 写作中 <p>About ongoing</p></article>
<article class="writing-entry" data-essay-url="/blogs/old/" data-essay-status="complete"><a href="/blogs/old/">old</a><p>About old</p></article>""")
        self.write_html("blogs/ongoing", """
<title>ongoing | Adrian</title><meta name="description" content="About ongoing">
<article class="chinese-essay" data-essay-status="writing"><time datetime="2026-09-01T00:00:00+00:00">2026-09-01</time></article>
<a href="/blogs/old/" rel="prev">old</a>""")
        self.write_html("blogs/old", """
<title>old | Adrian</title><meta name="description" content="About old">
<article class="chinese-essay" data-essay-status="complete"><time datetime="2020-01-01T00:00:00+00:00">2020-01-01</time><time datetime="2026-09-16T00:00:00+00:00">2026-09-16</time></article>
<a href="/blogs/ongoing/" rel="next">ongoing</a>""")
        self.feed = ElementTree.fromstring("""
<feed xmlns="http://www.w3.org/2005/Atom">
  <updated>2026-09-16T00:00:00+00:00</updated>
  <entry><id>https://example.com/blogs/old/</id><title>old</title><summary>About old</summary><published>2020-01-01T00:00:00+00:00</published><updated>2026-09-16T00:00:00+00:00</updated></entry>
  <entry><id>https://example.com/blogs/ongoing/</id><title>ongoing</title><summary>About ongoing</summary><published>2026-09-01T00:00:00+00:00</published><updated>2026-09-01T00:00:00+00:00</updated></entry>
</feed>""")

    def check_output(self):
        essays, errors = load_essays(self.source)
        self.assertEqual([], errors)
        pages = {path: Page(path) for path in self.build.rglob("*.html")}
        return check_essay_output(essays, pages, self.feed, self.build, {"example.com"})

    def test_public_ongoing_and_old_update_are_included_but_draft_is_hidden(self):
        self.assertEqual([], self.check_output())

    def test_a_generated_or_linked_draft_is_rejected(self):
        self.write_html("blogs/draft", "<h1>draft</h1>")
        with self.index_path.open("a", encoding="utf-8") as output:
            output.write('<a href="/blogs/draft/">draft</a>')
        errors = self.check_output()
        self.assertTrue(any("draft appears in build" in error for error in errors), errors)
        self.assertTrue(any("links to private draft" in error for error in errors), errors)

    def test_missing_ongoing_article_in_index_is_rejected(self):
        self.index_path.write_text('<article class="writing-entry" data-essay-url="/blogs/old/" data-essay-status="complete"><a href="/blogs/old/">old</a>About old</article>', encoding="utf-8")
        self.assertTrue(any("membership differs" in error for error in self.check_output()))

    def test_feed_must_order_by_update_and_preserve_original_publication_date(self):
        entries = self.feed.findall("{http://www.w3.org/2005/Atom}entry")
        self.feed.remove(entries[0])
        self.feed.append(entries[0])
        entries[0].find("{http://www.w3.org/2005/Atom}published").text = "2026-09-16T00:00:00+00:00"
        errors = self.check_output()
        self.assertTrue(any("most recently updated" in error for error in errors), errors)
        self.assertTrue(any("published differs" in error for error in errors), errors)

    def test_date_only_sources_accept_windows_fixed_offset_serialization(self):
        # Native Windows Ruby may use the current +10 offset for a January
        # calendar date that tzdata would resolve with a historical +11 offset.
        config = self.source / "_config.yml"
        config.write_text(config.read_text(encoding="utf-8").replace("timezone: UTC", "timezone: Australia/Sydney"), encoding="utf-8")
        for element in self.feed.iter():
            if element.tag.endswith(("}published", "}updated")):
                element.text = element.text.replace("+00:00", "+10:00")
        self.assertEqual([], self.check_output())
        old_published = self.feed.findall("{http://www.w3.org/2005/Atom}entry")[0].find("{http://www.w3.org/2005/Atom}published")
        old_published.text = "2020-01-02T00:00:00+10:00"
        self.assertTrue(any("published differs" in error for error in self.check_output()))

    def test_explicit_timestamps_still_require_the_correct_instant(self):
        self.write_essay("ongoing", "2026-09-01T00:00:00+00:00", "status: writing\n")
        self.write_essay("old", "2020-01-01", "last_modified_at: 2026-09-16T00:00:00+00:00\n")
        for element in self.feed.iter():
            if element.tag.endswith(("}published", "}updated")):
                element.text = element.text.replace("+00:00", "+10:00")
        errors = self.check_output()
        self.assertTrue(any("/blogs/ongoing/ published differs" in error for error in errors), errors)
        self.assertTrue(any("/blogs/ongoing/ updated differs" in error for error in errors), errors)
        self.assertTrue(any("/blogs/old/ updated differs" in error for error in errors), errors)
        self.assertTrue(any("feed updated timestamp must match" in error for error in errors), errors)

    def test_reversed_adjacent_article_links_are_rejected(self):
        old_page = self.build / "blogs/old/index.html"
        old_page.write_text(old_page.read_text(encoding="utf-8").replace('rel="next"', 'rel="prev"'), encoding="utf-8")
        self.assertTrue(any("rel=next" in error for error in self.check_output()))

    def test_metadata_errors_fail_before_publication(self):
        for extra, expected in (("layout: page\n", "layout must resolve"),
                                ("status: hidden\n", "status must be"),
                                ('published: "false"\n', "published must be"),
                                ("last_modified_at: 2019-01-01\n", "must not be earlier"),
                                ("title: duplicate\n", "duplicate YAML field")):
            with self.subTest(expected=expected):
                self.write_essay("invalid", "2026-01-01", extra)
                _, errors = load_essays(self.source)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_duplicate_canonical_permalink_is_rejected(self):
        path = self.source / "blogs/draft.md"
        path.write_text(path.read_text(encoding="utf-8").replace("/blogs/draft/", "/blogs/old/index.html"), encoding="utf-8")
        _, errors = load_essays(self.source)
        self.assertTrue(any("duplicate permalink" in error for error in errors), errors)

    def test_draft_generator_quotes_titles_and_refuses_overwrite_or_path_escape(self):
        path = create_essay(self.source, "new-essay", '标题: "引号"', "", date(2026, 9, 16))
        essays, errors = load_essays(self.source)
        self.assertEqual([], errors)
        generated = next(essay for essay in essays if essay.source == "blogs/new-essay.md")
        self.assertFalse(generated.public)
        self.assertEqual("writing", generated.status)
        self.assertEqual('标题: "引号"', generated.title)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            create_essay(self.source, "new-essay", "replacement", "", date.today())
        self.assertEqual(original, path.read_bytes())
        with self.assertRaises(ValueError):
            create_essay(self.source, "../escape", "title", "", date.today())
        path.write_text(path.read_text(encoding="utf-8").replace("published: false", "published: true"), encoding="utf-8")
        _, errors = load_essays(self.source)
        self.assertTrue(any("description must be a nonempty" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
