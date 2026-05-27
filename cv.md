---
layout: page
permalink: /cv/index.html
title: CV
---

Latest Update: 26th May, 2026

## Curriculum Vitae
<p style="text-align:center; margin: 1.5em 0 2.2em;">
  <a class="cv-btn cv-btn-primary" href="{{ site.url }}/file/CV-ChunyangZhang-UNSW.pdf" download>
    Download PDF
  </a>
  <a class="cv-btn cv-btn-ghost" href="{{ site.url }}/file/CV-ChunyangZhang-UNSW.pdf" target="_blank" rel="noopener">
    Open in New Tab
  </a>
</p>

<div class="cv-preview">
  <object data="{{ site.url }}/file/CV-ChunyangZhang-UNSW.pdf#view=FitH" type="application/pdf">
    <p style="text-align:center; padding: 2em;">
      Your browser does not support inline PDF preview.
      <a href="{{ site.url }}/file/CV-ChunyangZhang-UNSW.pdf">Download the PDF instead</a>.
    </p>
  </object>
</div>

<style>
  .cv-btn {
    display: inline-block;
    padding: 10px 22px;
    margin: 0 6px 8px;
    border-radius: 8px;
    font-weight: 600;
    text-decoration: none;
    border: 2px solid var(--color-accent);
    transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
  }
  .cv-btn-primary {
    background: var(--color-accent);
    color: #fff !important;
    box-shadow: 0 4px 14px rgba(59, 185, 255, 0.35);
  }
  .cv-btn-primary:hover {
    background: var(--color-accent-dark);
    border-color: var(--color-accent-dark);
    color: #fff !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(59, 185, 255, 0.45);
  }
  .cv-btn-ghost {
    color: var(--color-accent-dark);
    background: transparent;
  }
  .cv-btn-ghost:hover {
    background: var(--color-accent-soft);
    color: var(--color-accent-dark);
    transform: translateY(-2px);
  }
  /* Remove the article-wrap link underline-on-hover from these buttons */
  .article-wrap .cv-btn { border-bottom: none !important; }

  .cv-preview {
    max-width: 900px;
    margin: 0 auto;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--color-border);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
  }
  .cv-preview object { width: 100%; height: 1100px; display: block; }
</style>
