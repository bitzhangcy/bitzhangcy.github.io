---
layout: page
permalink: /projects/index.html
title: Projects
eyebrow: Research directions
description: "Adrian's research projects in controllable generation, multimodal reasoning, and learning for industrial and dynamical systems."
---

<p class="section-intro">My research builds on industrial and nonlinear control and is expanding toward large language models, multimodal reasoning, and generative systems. These projects explore how learned models can support perception, modeling, and decision making.</p>

## Public Research

<div class="project-list">
  <article class="project-entry" id="attention-specialty-tuning">
    <p class="project-meta"><span class="tag">Preprint · 2025</span> Controllable image generation</p>
    <h3><a href="https://arxiv.org/abs/2504.10148">Hierarchical and Step-Layer-Wise Tuning of Attention Specialty for Multi-Instance Synthesis in Diffusion Transformers</a></h3>
    <p class="project-description">Generating several distinct objects in one image requires control over their placement and individual attributes. This work studies how different token types are represented across diffusion-transformer layers and introduces training-free attention specialty tuning to guide multi-instance synthesis across layers and denoising steps.</p>
    <figure class="project-figure">
      <a href="{{ '/images/research/ast-overview.svg' | relative_url }}" aria-label="View the attention specialty tuning diagram at full size">
        <img src="{{ '/images/research/ast-overview.svg' | relative_url }}" alt="Method diagram showing attention specialty tuning, masks derived from prompts and spatial layouts, and token-specific tuning across transformer layers and denoising steps." width="3064" height="1262" loading="lazy" decoding="async">
      </a>
      <figcaption>Attention specialty tuning and hierarchical control across layers and steps. <a href="https://arxiv.org/html/2504.10148v2#S3.F4">Figure 4, Zhang et al. (2025)</a> · <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA 4.0</a>.</figcaption>
    </figure>
    <p class="publication-links"><a href="https://arxiv.org/abs/2504.10148">Paper</a><a href="https://arxiv.org/pdf/2504.10148">PDF</a><a href="{{ '/publications/' | relative_url }}">Publication details</a></p>
  </article>
</div>

## Current Research

<p class="section-intro">The following projects are in progress.</p>

### Generative Models &amp; Multimodal Reasoning

<div class="project-list">
  <article class="project-entry">
    <h4>Training-Free Consistent Synthesis and Editing in Diffusion Transformers</h4>
    <p class="project-description">Exploring training-free methods to preserve identity and structure during image generation and editing.</p>
  </article>

  <article class="project-entry">
    <h4>Learnable Persistent Memory Router for Narrative Long Multi-Shot Video Generation</h4>
    <p class="project-description">Investigating persistent memory mechanisms to maintain coherence across shots in long-form video generation.</p>
  </article>

  <article class="project-entry">
    <h4>VLM-Based Multi-Agent Systems for Long and Complex Video Understanding</h4>
    <p class="project-description">Exploring how cooperating vision-language models can reason over long videos and connect information across events.</p>
  </article>
</div>

### Learning for Energy &amp; Dynamical Systems

<div class="project-list">
  <article class="project-entry">
    <h4>Conditional Flow Matching for Multivariate Energy Profile Imputation</h4>
    <p class="project-description">Investigating conditional generative models for filling missing values in multivariate energy profiles.</p>
  </article>

  <article class="project-entry">
    <h4>Optimal Control of Infinite-Dimensional Systems via Neural Operators</h4>
    <p class="project-description">Exploring neural-operator methods for modeling and controlling systems whose dynamics vary over space and time.</p>
  </article>
</div>
