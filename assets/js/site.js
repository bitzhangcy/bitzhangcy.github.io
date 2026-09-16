/* Navigation and reading aids progressively enhance fully usable HTML. */
(function () {
  'use strict';
  var header = document.querySelector('.site-header');
  var headerHeight = 0;
  var refreshReadingPosition = function () {};
  function measureHeader() {
    if (!header) return;
    var measured = Math.ceil(header.getBoundingClientRect().height);
    if (measured === headerHeight) return;
    headerHeight = measured;
    document.documentElement.style.setProperty('--header-height', measured + 'px');
    refreshReadingPosition();
  }
  measureHeader();
  if (header && 'ResizeObserver' in window) new ResizeObserver(measureHeader).observe(header);
  else window.addEventListener('resize', measureHeader);

  var toggle = document.querySelector('.nav-toggle');
  var navigation = document.getElementById('site-navigation');
  var mobile = window.matchMedia('(max-width: 700px)');
  if (toggle && navigation) {
    function closeMenu() {
      navigation.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      measureHeader();
    }
    toggle.addEventListener('click', function () {
      var opened = navigation.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(opened));
      measureHeader();
    });
    navigation.addEventListener('click', function (event) {
      if (event.target.closest('a') && mobile.matches) closeMenu();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && mobile.matches && navigation.classList.contains('is-open')) {
        closeMenu();
        toggle.focus();
      }
    });
    document.addEventListener('click', function (event) {
      if (mobile.matches && !event.target.closest('.site-header')) closeMenu();
    });
    function resetAtBreakpoint() {
      if (!mobile.matches && document.activeElement === toggle) navigation.querySelector('a').focus();
      if (mobile.matches && navigation.contains(document.activeElement)) toggle.focus();
      closeMenu();
    }
    if (mobile.addEventListener) mobile.addEventListener('change', resetAtBreakpoint);
    else mobile.addListener(resetAtBreakpoint);
    navigation.classList.add('nav-enhanced');
    document.querySelector('.site-header').classList.add('nav-ready');
    toggle.hidden = false;
    measureHeader();
  }

  var topButton = document.getElementById('back-to-top');
  if (topButton) {
    function updateTopButton() { topButton.hidden = window.scrollY < 500; }
    window.addEventListener('scroll', updateTopButton, { passive: true });
    updateTopButton();
    topButton.addEventListener('click', function () {
      var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var main = document.getElementById('main');
      if (main) main.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  }

  var readingTools = document.querySelector('.reading-tools');
  var readingSearch = document.getElementById('reading-search');
  var yearNavigation = document.querySelector('.reading-page .year-nav');
  if (readingTools && readingSearch && yearNavigation) {
    var readingClear = readingTools.querySelector('.reading-search-clear');
    var readingCount = document.getElementById('reading-result-count');
    var readingEmpty = document.querySelector('.reading-empty');
    var readingYears = [];
    var totalReadings = 0;

    function normalizeSearch(value) {
      return value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
    }

    yearNavigation.querySelectorAll('a').forEach(function (yearLink) {
      var heading = document.getElementById(decodeURIComponent(yearLink.hash.slice(1)));
      if (!heading || heading.tagName !== 'H2') return;
      if (!heading.hasAttribute('tabindex')) heading.setAttribute('tabindex', '-1');
      var section = document.createElement('section');
      section.className = 'reading-year';
      section.setAttribute('aria-labelledby', heading.id);
      heading.parentNode.insertBefore(section, heading);
      var next = heading.nextElementSibling;
      section.appendChild(heading);
      while (next && next.tagName !== 'H2') {
        var following = next.nextElementSibling;
        section.appendChild(next);
        next = following;
      }
      var entries = [];
      Array.prototype.forEach.call(section.children, function (child) {
        if (child.tagName !== 'UL' && child.tagName !== 'OL') return;
        Array.prototype.forEach.call(child.children, function (item) {
          if (item.tagName !== 'LI') return;
          var title = item.querySelector('a');
          if (!title) {
            title = item.cloneNode(true);
            title.querySelectorAll('ul, ol').forEach(function (notes) { notes.remove(); });
          }
          entries.push({ element: item, title: normalizeSearch(title.textContent) });
        });
      });
      totalReadings += entries.length;
      readingYears.push({ section: section, link: yearLink, entries: entries });
    });

    function filterReadings() {
      var query = normalizeSearch(readingSearch.value);
      var terms = query ? query.split(' ') : [];
      var visibleCount = 0;
      readingYears.forEach(function (year) {
        var yearCount = 0;
        year.entries.forEach(function (entry) {
          var matches = terms.every(function (term) { return entry.title.indexOf(term) !== -1; });
          entry.element.hidden = !matches;
          if (matches) yearCount += 1;
        });
        year.section.hidden = yearCount === 0;
        year.link.hidden = yearCount === 0;
        visibleCount += yearCount;
      });
      readingClear.hidden = !readingSearch.value;
      readingEmpty.hidden = visibleCount !== 0;
      yearNavigation.hidden = visibleCount === 0;
      readingCount.textContent = query
        ? '找到 ' + visibleCount + ' 条，共 ' + totalReadings + ' 条记录'
        : '共 ' + totalReadings + ' 条阅读记录';
    }

    readingSearch.addEventListener('input', function (event) {
      if (!event.isComposing) filterReadings();
    });
    readingSearch.addEventListener('compositionend', filterReadings);
    readingClear.addEventListener('click', function () {
      readingSearch.value = '';
      filterReadings();
      readingSearch.focus();
    });
    readingSearch.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && readingSearch.value && !event.isComposing) {
        event.preventDefault();
        readingSearch.value = '';
        filterReadings();
      }
    });
    readingTools.hidden = false;
    filterReadings();
  }

  var toc = document.querySelector('.essay-toc');
  var headings = document.querySelectorAll('.essay-body h2, .essay-body h3');
  if (toc && headings.length >= 3) {
    var list = document.createElement('ol');
    var tocLinks = [];
    var wideEssay = window.matchMedia('(min-width: 1200px)');
    var tocSummary = toc.querySelector('summary');
    headings.forEach(function (heading, index) {
      if (!heading.id) {
        var identifier = 'essay-section-' + (index + 1);
        while (document.getElementById(identifier)) identifier += '-section';
        heading.id = identifier;
      }
      // Native fragment navigation now moves keyboard focus into the essay.
      if (!heading.hasAttribute('tabindex')) heading.setAttribute('tabindex', '-1');
      var item = document.createElement('li');
      if (heading.tagName === 'H3') item.className = 'toc-subheading';
      var link = document.createElement('a');
      link.href = '#' + encodeURIComponent(heading.id);
      link.textContent = heading.textContent;
      tocLinks.push(link);
      item.appendChild(link);
      list.appendChild(item);
    });
    toc.querySelector('nav').appendChild(list);
    toc.closest('.chinese-essay').classList.add('has-toc');
    toc.hidden = false;

    var headingPositions = [];
    var activeIndex = -1;
    var tocFrame = 0;
    var positionsDirty = true;

    function updateActiveSection() {
      tocFrame = 0;
      if (positionsDirty) {
        headingPositions = Array.prototype.map.call(headings, function (heading) {
          return heading.getBoundingClientRect().top + window.scrollY;
        });
        positionsDirty = false;
      }
      // Native fragment alignment combines the scroll container's padding and target margin.
      var scrollPadding = parseFloat(window.getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      var scrollMargin = parseFloat(window.getComputedStyle(headings[0]).scrollMarginTop) || 0;
      var offset = scrollPadding + scrollMargin;
      offset = Math.max(offset, headerHeight + (wideEssay.matches ? 0 : tocSummary.getBoundingClientRect().height) + 24);
      var position = window.scrollY + offset + 2;
      var selected = 0;
      for (var index = 0; index < headingPositions.length; index += 1) {
        if (headingPositions[index] <= position) selected = index;
        else break;
      }
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
        selected = headings.length - 1;
      }
      if (selected !== activeIndex) {
        if (activeIndex !== -1) tocLinks[activeIndex].removeAttribute('aria-current');
        tocLinks[selected].setAttribute('aria-current', 'location');
        activeIndex = selected;
        // Keep the current chapter visible within a long sidebar, without
        // changing the essay's scroll position or a reader's keyboard focus.
        var tocNav = toc.querySelector('nav');
        if (wideEssay.matches && toc.open && !tocNav.contains(document.activeElement)) {
          var navBounds = tocNav.getBoundingClientRect();
          var linkBounds = tocLinks[selected].getBoundingClientRect();
          if (linkBounds.top < navBounds.top) tocNav.scrollTop -= navBounds.top - linkBounds.top;
          else if (linkBounds.bottom > navBounds.bottom) tocNav.scrollTop += linkBounds.bottom - navBounds.bottom;
        }
      }
    }

    function scheduleTocUpdate(remeasure) {
      if (remeasure) positionsDirty = true;
      if (!tocFrame) tocFrame = window.requestAnimationFrame(updateActiveSection);
    }

    refreshReadingPosition = function () { scheduleTocUpdate(true); };

    function resetTocAtBreakpoint() {
      if (!wideEssay.matches && toc.querySelector('nav').contains(document.activeElement)) tocSummary.focus();
      toc.open = wideEssay.matches;
      scheduleTocUpdate(true);
    }

    toc.addEventListener('click', function (event) {
      var link = event.target.closest('nav a');
      if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      if (!wideEssay.matches) toc.open = false;
      // Do not intercept the anchor: the browser handles URL, history and focus.
      scheduleTocUpdate(true);
    });
    toc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !wideEssay.matches && toc.open) {
        toc.open = false;
        tocSummary.focus();
      }
    });
    toc.addEventListener('toggle', function () { scheduleTocUpdate(true); });
    window.addEventListener('scroll', function () { scheduleTocUpdate(false); }, { passive: true });
    window.addEventListener('resize', function () { scheduleTocUpdate(true); });
    window.addEventListener('load', function () { scheduleTocUpdate(true); });
    window.addEventListener('hashchange', function () { scheduleTocUpdate(false); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { scheduleTocUpdate(true); });
    if (wideEssay.addEventListener) wideEssay.addEventListener('change', resetTocAtBreakpoint);
    else wideEssay.addListener(resetTocAtBreakpoint);
    resetTocAtBreakpoint();
  }
}());
