# Adrian's personal website

A Jekyll website for Adrian's research, publications, projects, CV, Chinese essays, and reading notes. The public site is [chunyangzhang.com](https://chunyangzhang.com).

## Local setup

Use Ruby 3.3 with Bundler. On Windows, install Ruby+Devkit and its MSYS2 development toolchain as described in the [official Jekyll guide](https://jekyllrb.com/docs/installation/windows/); some preview dependencies have native extensions. Use Python 3.10 or newer for the article generator and site checks. The checker uses PyYAML to read front matter and tzdata for consistent timezone handling on Windows.

From the repository root:

```text
bundle config set --local path vendor/bundle
bundle install
python -m pip install -r scripts/requirements.txt
```

The Gemfile uses Jekyll 3.10 and jekyll-sitemap 1.4, matching the site's relevant [GitHub Pages dependencies](https://pages.github.com/versions/). Metadata and the writing feed are maintained in the site templates. After changing Ruby versions, run `bundle install` again to resolve dependencies for the new runtime.

## Preview and check

```text
bundle exec jekyll serve --destination _site-preview --host 127.0.0.1 --port 4000
```

Open [localhost:4000](http://127.0.0.1:4000). Jekyll rebuilds pages after content and style changes; restart it after changing `_config.yml`. Stop the server with `Ctrl+C`.

For a one-time build and local link/structure checks:

```text
bundle exec jekyll build --destination _site-preview
python scripts/check_site.py _site-preview
```

The checker examines local links and anchors, HTML and CSS assets, document metadata, headings, main landmarks, image alt attributes, JSON-LD, the Atom feed, the root 404 page, and excluded development/draft files. It also reads the essay source metadata, verifies public articles appear in Writing and the appropriate feed entries, checks previous/next links, and makes sure private drafts are neither generated nor linked. It does not contact external links or replace desktop and mobile visual inspection.

For a quick article metadata check without building, run `python scripts/check_site.py --source-only`. To test the publishing checks, run `python -m unittest discover -s scripts -p "test_*.py"`.

Analytics load only when `JEKYLL_ENV=production`. In `_config.yml`, `analytics.provider` chooses exactly one provider: `google` (the default), `counter`, or `baidu`; set it to `""` to disable analytics. Existing account IDs are retained under their respective keys so switching providers needs only one edit.

For a production-mode build in PowerShell:

```powershell
$env:JEKYLL_ENV = 'production'
bundle exec jekyll build --destination _site-production
python scripts/check_site.py _site-production
Remove-Item Env:JEKYLL_ENV
```

On macOS or Linux, use `JEKYLL_ENV=production bundle exec jekyll build --destination _site-production` for that build. Local builds do not publish the website. The repository's existing GitHub Pages settings control publication.

The **Check site** GitHub Actions workflow runs the publishing-rule tests, a production Jekyll build, and these checks on pushes and pull requests; it can also be run manually from the Actions tab. It has read-only repository permissions and does not deploy. Existing GitHub Pages publication remains separate; making this check a required branch check is an optional repository setting.

Build folders, local tools, caches, and installed dependencies are ignored by Git and excluded from the generated site. The existing `_site` folder may be stale; use a fresh `_site-preview` build for review.

## Editing content

| File or folder | Purpose |
| --- | --- |
| `index.md` | Introduction, contact links, research interests, news, and education |
| `publications.md` | Publication records and available paper links |
| `projects.md` | Public projects and current research |
| `cv.md`, `file/` | Compatibility redirect for the old CV URL and downloadable documents |
| `personal-blogs.md`, `blogs/` | Writing index and Chinese essays |
| `readings.md` | Reading history |
| `_config.yml` | Identity, navigation, site URL, analytics, and build exclusions |
| `_layouts/`, `_includes/` | Shared page structure, navigation, metadata, and footer |
| `assets/css/`, `assets/js/` | Responsive styles and progressive enhancements |
| `feed.xml` | Atom feed generated from published essay pages |

Keep files encoded as UTF-8 without a byte-order mark. Use `relative_url` for site links and assets, and `absolute_url` for canonical and share URLs; the production domain can remain in `_config.yml` during local previews.

The CV link in the homepage contact area opens `file/CV-ChunyangZhang-UNSW.pdf` directly. CV is not a primary navigation item. The old `/cv/` URL remains as an immediate, JavaScript-free redirect with a manual PDF link for compatibility. It is excluded from the sitemap and search indexing; there is no separate CV display page or embedded viewer.

Create a new essay from the repository root:

```text
python scripts/new_essay.py reading-history "文章标题"
```

This creates `blogs/reading-history.md` as a private draft. The slug uses lowercase letters, numbers, and hyphens; existing files are never overwritten. Optionally pass `--description "一句话简介"` and `--date 2026-09-16`; otherwise the date is your computer's local date. The generator uses only the Python standard library.

Edit the front matter at the top of the new file:

```yaml
---
layout: essay
title: "Article title"
description: "A brief description of the article."
date: 2026-09-16
permalink: /blogs/article-slug/
lang: zh-CN
locale: zh_CN
published: false
status: writing
# last_modified_at: 2026-09-16
---
```

The three states are independent of article length:

| State | Front matter | Result |
| --- | --- | --- |
| Private draft | `published: false`, `status: writing` | No generated article, Writing entry, or feed entry |
| Public and still being written | `published: true`, `status: writing` | Public article with a visible “写作中” label |
| Public and complete | `published: true`, `status: complete` | Public article without the in-progress label |

To publish, fill in `title`, a one-sentence `description`, `date`, and a unique `permalink`, then change only `published: false` to `published: true`. Leave `status: writing` while adding sections; change it to `complete` when finished. Existing essays may omit `published` and `status`, which means public and complete. Defaults under `blogs/` provide the essay layout and Chinese language metadata; the explicit fields in generated drafts keep each file easy to understand.

Keep `date` as the original publication date. On a substantive update, add or change `last_modified_at: YYYY-MM-DD` (it must be on or after `date`). Writing and previous/next navigation remain sorted by publication date; the Atom feed contains the 10 most recently updated public articles, so updating an older article can bring it back into the feed. Publication and update dates are shown separately on the article. Dates without a timezone use the site's `Australia/Sydney` timezone. A future date does not make a regular Jekyll page private; use `published: false` to keep a draft unpublished.

The essay layout provides the main title; begin article sections with `##`. Do not add a duplicate `#` title or put individual drafts in `_config.yml`'s `exclude` list. There is no minimum article length. The site builds a table of contents when at least three `##`/`###` headings exist; shorter articles still appear normally in Writing.

`published: false` excludes the article from the generated website, but the source file remains visible if it is committed to this public repository. Keep any genuinely private material outside the repository.

## Credits

Originally adapted from [GuangLun2000's website](https://github.com/GuangLun2000/GuangLun2000.github.io), with roots in the [Minimal Mistakes](https://mademistakes.com/) theme. Built with [Jekyll](https://jekyllrb.com/) and hosted on [GitHub Pages](https://pages.github.com/). See [LICENSE](LICENSE).
