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

<p class="writing-subscribe"><a href="{{ '/feed.xml' | relative_url }}">订阅文章更新 <span aria-hidden="true">↗</span></a></p>

<div class="writing-list">
  {% assign essays = site.pages | where: 'layout', 'essay' | where_exp: 'essay', 'essay.published != false' | sort: 'date' | reverse %}
  {% for essay in essays %}
  <article class="writing-entry" data-essay-status="{{ essay.status | default: 'complete' }}" data-essay-url="{{ essay.url | relative_url }}">
    <p class="writing-year"><time datetime="{{ essay.date | date: '%Y' }}">{{ essay.date | date: '%Y' }}</time></p>
    <h2><a href="{{ essay.url | relative_url }}">{{ essay.title | escape | replace: '：', '：<wbr>' | replace: '——', '——<wbr>' }}</a>{% if essay.status == 'writing' %} <span class="essay-status">写作中</span>{% endif %}</h2>
    <p class="writing-description">{{ essay.description | escape }}</p>
  </article>
  {% endfor %}
</div>
