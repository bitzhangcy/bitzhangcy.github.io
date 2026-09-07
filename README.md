# Adrian's personal website

A Jekyll website for Adrian's research, publications, projects, CV, Chinese essays, and reading notes. The public site is [chunyangzhang.com](https://chunyangzhang.com).

## Local setup

Use Ruby 3.3 with Bundler. On Windows, install Ruby+Devkit and its MSYS2 development toolchain as described in the [official Jekyll guide](https://jekyllrb.com/docs/installation/windows/); some preview dependencies have native extensions. Python 3.10 or newer is optional and is used only for the site checks below.

From the repository root:

```text
bundle config set --local path vendor/bundle
bundle install
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

The checker examines local links and anchors, HTML and CSS assets, document metadata, headings, main landmarks, image alt attributes, JSON-LD, the Atom feed, the root 404 page, and excluded development/draft files. It does not contact external links or replace desktop and mobile visual inspection.

Analytics load only when `JEKYLL_ENV=production`. For a production-mode build in PowerShell:

```powershell
$env:JEKYLL_ENV = 'production'
bundle exec jekyll build --destination _site-production
python scripts/check_site.py _site-production
Remove-Item Env:JEKYLL_ENV
```

On macOS or Linux, use `JEKYLL_ENV=production bundle exec jekyll build --destination _site-production` for that build. Local builds do not publish the website. The repository's existing GitHub Pages settings control publication.

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

For a new essay, add a Markdown file under `blogs/` with front matter such as:

```yaml
---
layout: essay
title: "Article title"
description: "A brief description of the article."
date: 2026-09-07
permalink: /blogs/article-slug/
lang: zh-CN
locale: zh_CN
---
```

The essay layout provides the main title; begin article sections with `##`. Published essays appear automatically in the writing index and feed. Keep incomplete articles excluded in `_config.yml` or mark them `published: false` until ready. The existing local draft `blogs/26ymxx.md` is explicitly excluded and has not been edited or published.

## Credits

Originally adapted from [GuangLun2000's website](https://github.com/GuangLun2000/GuangLun2000.github.io), with roots in the [Minimal Mistakes](https://mademistakes.com/) theme. Built with [Jekyll](https://jekyllrb.com/) and hosted on [GitHub Pages](https://pages.github.com/). See [LICENSE](LICENSE).
