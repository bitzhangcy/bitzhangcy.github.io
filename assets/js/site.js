/* Navigation and reading aids progressively enhance fully usable HTML. */
(function () {
  'use strict';
  var toggle = document.querySelector('.nav-toggle');
  var navigation = document.getElementById('site-navigation');
  var mobile = window.matchMedia('(max-width: 700px)');
  if (toggle && navigation) {
    function closeMenu() {
      navigation.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
    toggle.addEventListener('click', function () {
      var opened = navigation.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(opened));
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

  var toc = document.querySelector('.essay-toc');
  var headings = document.querySelectorAll('.essay-body h2, .essay-body h3');
  if (toc && headings.length >= 3) {
    var list = document.createElement('ol');
    headings.forEach(function (heading, index) {
      if (!heading.id) {
        var identifier = 'essay-section-' + (index + 1);
        while (document.getElementById(identifier)) identifier += '-section';
        heading.id = identifier;
      }
      var item = document.createElement('li');
      if (heading.tagName === 'H3') item.className = 'toc-subheading';
      var link = document.createElement('a');
      link.href = '#' + encodeURIComponent(heading.id);
      link.textContent = heading.textContent;
      item.appendChild(link);
      list.appendChild(item);
    });
    toc.querySelector('nav').appendChild(list);
    toc.hidden = false;
  }
}());
