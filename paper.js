/* paper.js — Reading enhancement layer for research.momentum.inc
   Auto-generates: reading progress bar, sticky nav, floating TOC.
   Works with any paper structure by detecting headings in the DOM. */

(function () {
  'use strict';

  /* ── Detect content container ── */
  var content =
    document.querySelector('.essay-body') ||
    document.querySelector('.article-body') ||
    document.querySelector('.doc-body') ||
    document.querySelector('main') ||
    document.querySelector('article');
  if (!content) return;

  /* ── Detect paper title ── */
  var titleEl =
    document.querySelector('.essay-title') ||
    document.querySelector('.article-title') ||
    document.querySelector('.doc-title') ||
    document.querySelector('h1');
  var paperTitle = titleEl ? titleEl.textContent.trim() : document.title;

  /* ── 0. Remove duplicate title inside article-body ── */
  /* Google Docs compiler injects the title as an h1 inside the body,
     duplicating the article-header title. Remove it. */
  var bodyFirstH1 = content.querySelector('h1');
  if (bodyFirstH1 && titleEl && bodyFirstH1 !== titleEl) {
    var bodyTitle = bodyFirstH1.textContent.trim().replace(/\s+/g, ' ');
    var headerTitle = paperTitle.replace(/\s+/g, ' ');
    if (bodyTitle === headerTitle) {
      /* Also remove the next sibling if it's a redundant byline */
      var next = bodyFirstH1.nextElementSibling;
      if (next && next.tagName === 'P' && /Raeez Lorgat/.test(next.textContent)) {
        next.remove();
      }
      bodyFirstH1.remove();
    }
  }

  /* ── 1. Reading progress bar ── */
  var progress = document.createElement('div');
  progress.className = 'reading-progress';
  progress.setAttribute('aria-hidden', 'true');
  document.body.appendChild(progress);

  /* ── 2. Sticky nav (appears on scroll) — skip if page has its own site header ── */
  var hasSiteHeader = !!document.querySelector('.site-header');
  var nav = null;
  if (!hasSiteHeader) {
    nav = document.createElement('nav');
    nav.className = 'paper-nav';
    nav.setAttribute('aria-label', 'Paper navigation');
    nav.innerHTML =
      '<a href="/">&larr; Research</a>' +
      '<span class="paper-nav-title">' + escHtml(paperTitle) + '</span>';
    document.body.appendChild(nav);
  }

  /* ── 3. Collect headings for TOC ── */
  var headings = [];
  var els = content.querySelectorAll('h1, h2, h3');
  var idCounter = 0;

  for (var i = 0; i < els.length; i++) {
    var el = els[i];
    var tag = el.tagName.toLowerCase();
    var text = el.textContent.trim();

    /* Skip very short or empty headings */
    if (text.length < 3) continue;
    /* Skip the first h1 if it matches the paper title (avoid duplication) */
    if (tag === 'h1' && i === 0 && text === paperTitle) continue;

    /* Ensure heading has an ID for anchor linking */
    if (!el.id) {
      el.id = 'section-' + (++idCounter);
    }

    headings.push({ el: el, id: el.id, text: text, tag: tag });
  }

  /* ── 4. Build floating TOC (if enough headings) ── */
  var toc = null;
  var tocToggle = null;
  var tocExpanded = true;

  if (headings.length >= 3) {
    /* TOC panel */
    toc = document.createElement('div');
    toc.className = 'floating-toc';
    toc.setAttribute('aria-label', 'Table of contents');

    var label = document.createElement('span');
    label.className = 'floating-toc-label';
    label.textContent = 'Contents';
    toc.appendChild(label);

    var ol = document.createElement('ol');

    /* Determine the shallowest heading level present */
    var minLevel = 9;
    for (var j = 0; j < headings.length; j++) {
      var lvl = parseInt(headings[j].tag.charAt(1));
      if (lvl < minLevel) minLevel = lvl;
    }

    /* Limit to ~25 items for readability */
    var maxItems = 25;
    var shown = 0;

    for (var k = 0; k < headings.length && shown < maxItems; k++) {
      var h = headings[k];
      var level = parseInt(h.tag.charAt(1));

      /* Only show top 2 levels */
      if (level > minLevel + 1) continue;

      var li = document.createElement('li');
      if (level > minLevel) li.className = 'toc-h3';

      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = truncate(h.text, 50);
      a.setAttribute('data-heading-id', h.id);

      li.appendChild(a);
      ol.appendChild(li);
      shown++;
    }

    toc.appendChild(ol);
    document.body.appendChild(toc);

    /* Toggle button (shows when TOC is collapsed) */
    tocToggle = document.createElement('button');
    tocToggle.className = 'floating-toc-toggle';
    tocToggle.setAttribute('aria-label', 'Toggle table of contents');
    tocToggle.textContent = '\u2261'; /* hamburger-ish */
    tocToggle.addEventListener('click', function () {
      tocExpanded = !tocExpanded;
      toc.classList.toggle('visible', tocExpanded);
      tocToggle.classList.toggle('visible', !tocExpanded);
    });
    document.body.appendChild(tocToggle);

    /* Close TOC when clicking a link */
    toc.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && window.innerWidth < 768) {
        tocExpanded = false;
        toc.classList.remove('visible');
        tocToggle.classList.add('visible');
      }
    });
  }

  /* ── 5. Scroll handler — progress + nav + TOC highlighting ── */
  var docHeight, winHeight;
  var navThreshold = 200;
  var navVisible = false;
  var tocVisible = false;
  var activeLink = null;
  var ticking = false;

  function measure() {
    docHeight = document.documentElement.scrollHeight;
    winHeight = window.innerHeight;
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      var scrollY = window.scrollY;

      /* Progress */
      var pct = docHeight > winHeight
        ? (scrollY / (docHeight - winHeight)) * 100
        : 0;
      progress.style.width = Math.min(100, pct) + '%';

      /* Sticky nav */
      if (nav) {
        if (scrollY > navThreshold && !navVisible) {
          nav.classList.add('visible');
          navVisible = true;
        } else if (scrollY <= navThreshold && navVisible) {
          nav.classList.remove('visible');
          navVisible = false;
        }
      }

      /* TOC visibility */
      if (toc) {
        if (scrollY > navThreshold && !tocVisible) {
          toc.classList.add('visible');
          tocVisible = true;
        } else if (scrollY <= navThreshold && tocVisible) {
          toc.classList.remove('visible');
          tocVisible = false;
        }
      }

      /* TOC active heading */
      if (toc && headings.length > 0) {
        var current = null;
        for (var i = 0; i < headings.length; i++) {
          var rect = headings[i].el.getBoundingClientRect();
          if (rect.top <= winHeight * 0.3) {
            current = headings[i].id;
          }
        }
        if (current !== activeLink) {
          activeLink = current;
          var links = toc.querySelectorAll('a');
          for (var j = 0; j < links.length; j++) {
            links[j].classList.toggle(
              'active',
              links[j].getAttribute('data-heading-id') === current
            );
          }
        }
      }

      ticking = false;
    });
  }

  measure();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', measure, { passive: true });
  window.addEventListener('load', function () {
    measure();
    onScroll();
  });
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      measure();
      onScroll();
    });
  }

  /* Initial check (in case page loads scrolled) */
  onScroll();

  /* ── Helpers ── */
  function escHtml(str) {
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function truncate(str, max) {
    return str.length > max ? str.substring(0, max) + '\u2026' : str;
  }
})();
