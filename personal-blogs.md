---
layout: page
page_class: writing-page
permalink: /personal-blogs/index.html
title: Writing
title_lang: en
eyebrow: 随笔与思考
description: Adrian 的中文随笔，记录关于历史、政治制度与社会变迁的阅读和思考。
lang: zh-CN
locale: zh_CN
---

<p class="page-intro">科研之外，读历史，也读当下。这里记录我对历史、政治制度与社会变迁的一些思考。</p>

<div class="writing-list">
  {% assign essays = site.pages | where: 'layout', 'essay' | sort: 'date' | reverse %}
  {% for essay in essays %}
  <article class="writing-entry">
    <p class="writing-year"><time datetime="{{ essay.date | date: '%Y' }}">{{ essay.date | date: '%Y' }}</time></p>
    <h2><a href="{{ essay.url | relative_url }}">{{ essay.title | escape }}</a></h2>
    <p class="writing-description">{{ essay.description | escape }}</p>
  </article>
  {% endfor %}
</div>
