(function () {
  'use strict';

  // ── RESET UI STATE ON BACK/FORWARD NAVIGATION ──
  // Browsers restore a bfcache'd page exactly as it looked when you
  // navigated away (mobile menu open, command palette open, etc.)
  // instead of loading fresh -- DOMContentLoaded doesn't refire for
  // a bfcache restore, so this has to be a standalone listener, not
  // nested inside the DOMContentLoaded block below.
  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    const links = document.querySelector('.nav-links');
    if (links) links.classList.remove('open');
    const overlay = document.getElementById('cmdk-overlay');
    if (overlay) overlay.classList.remove('open');
  });

  document.addEventListener('DOMContentLoaded', function () {

    // ── NAV TOGGLE ──
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle) {
      toggle.addEventListener('click', function () {
        links.classList.toggle('open');
      });
    }

    // ── BACK BUTTON (avoids javascript: URLs, which CSP's script-src blocks) ──
    document.querySelectorAll('[data-back]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
        history.back();
      });
    });

    // ── NAV SCROLL STATE ──
    const siteNav = document.getElementById('site-nav');
    if (siteNav) {
      function updateNavScrolled() {
        siteNav.classList.toggle('scrolled', window.scrollY > 8);
      }
      updateNavScrolled();
      window.addEventListener('scroll', updateNavScrolled, { passive: true });
    }

    // ── CODE HEADER (lang label + copy button) ──
    document.querySelectorAll('.post-content .highlight').forEach(function (block) {
      const code = block.querySelector('code');
      const lang = code ? code.getAttribute('data-lang') : '';
      const pre = block.querySelector('pre');

      const header = document.createElement('div');
      header.className = 'code-header';

      const label = document.createElement('span');
      label.className = 'code-lang mono';
      const displayLang =
        lang === 'fallback' && code && code.innerText.includes('BEGIN PGP')
          ? 'pgp'
          : lang || 'code';
      label.textContent = displayLang;

      const btn = document.createElement('button');
      btn.className = 'copy-btn mono';
      btn.textContent = 'copy';

      header.appendChild(label);
      header.appendChild(btn);
      block.insertBefore(header, pre);

      btn.addEventListener('click', function () {
        navigator.clipboard
          .writeText(code ? code.innerText : pre.innerText)
          .then(function () {
            btn.textContent = 'copied';
            setTimeout(function () {
              btn.textContent = 'copy';
            }, 2000);
          });
      });
    });

    // ── COPY AS MARKDOWN ──
    const copyMdBtn = document.getElementById('copy-md-btn');
    if (copyMdBtn) {
      copyMdBtn.addEventListener('click', function () {
        const raw = document.getElementById('raw-markdown');
        if (!raw) return;
        const text = JSON.parse(raw.textContent);
        navigator.clipboard.writeText(text).then(function () {
          copyMdBtn.textContent = 'copied';
          setTimeout(function () {
            copyMdBtn.textContent = 'copy as markdown';
          }, 2000);
        });
      });
    }

    // ── SCROLL FADE-IN ──
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('.fade-in').forEach(function (el) {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight) {
        el.classList.add('visible');
      } else {
        observer.observe(el);
      }
    });

    // ── READING PROGRESS BAR ──
    const progressBar = document.getElementById('reading-progress-bar');
    const postContent = document.querySelector('.post-content');
    if (progressBar && postContent) {
      function updateProgress() {
        const rect = postContent.getBoundingClientRect();
        const total = rect.height - window.innerHeight;
        const scrolled = -rect.top;
        const pct = total > 0 ? Math.min(100, Math.max(0, (scrolled / total) * 100)) : 0;
        progressBar.style.width = pct + '%';
      }
      updateProgress();
      window.addEventListener('scroll', updateProgress, { passive: true });
      window.addEventListener('resize', updateProgress);
    }

    // ── SCROLL-SPY TOC ──
    const tocLinks = document.querySelectorAll('.toc-body a[href^="#"]');
    if (tocLinks.length) {
      const headingMap = new Map();
      tocLinks.forEach(function (link) {
        const id = link.getAttribute('href').slice(1);
        const heading = document.getElementById(id);
        if (heading) headingMap.set(heading, link);
      });

      const spy = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            const link = headingMap.get(entry.target);
            if (!link) return;
            if (entry.isIntersecting) {
              tocLinks.forEach(function (l) { l.classList.remove('active'); });
              link.classList.add('active');
            }
          });
        },
        { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
      );

      headingMap.forEach(function (link, heading) { spy.observe(heading); });
    }

  });

  // ── COMMAND PALETTE ──
  document.addEventListener('DOMContentLoaded', function () {
    const overlay = document.getElementById('cmdk-overlay');
    const input = document.getElementById('cmdk-input');
    const results = document.getElementById('cmdk-results');
    const trigger = document.getElementById('cmdk-trigger');
    const closeBtn = document.getElementById('cmdk-close');
    if (!overlay || !input || !results) return;

    let activeIndex = -1;
    let currentItems = [];
    let debounceTimer = null;

    function renderItems(items) {
      currentItems = items;
      activeIndex = -1;
      if (!items.length) {
        results.innerHTML = '<div class="cmdk-empty">no results</div>';
        return;
      }
      results.innerHTML = items.map(function (item, i) {
        return '<a href="' + item.url + '" class="cmdk-item" data-index="' + i + '">' +
          '<span class="cmdk-item-title">' + item.title + '</span>' +
          '<span class="cmdk-item-tag mono">' + item.tag + '</span>' +
          '</a>';
      }).join('');
    }

    function fetchResults(q) {
      fetch('/cmdk-search/?q=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(function (data) { renderItems(data.results || []); })
        .catch(function () { renderItems([]); });
    }

    function openPalette() {
      overlay.classList.add('open');
      input.value = '';
      input.focus();
      fetchResults('');
    }

    function closePalette() {
      overlay.classList.remove('open');
    }

    if (trigger) trigger.addEventListener('click', openPalette);
    if (closeBtn) closeBtn.addEventListener('click', closePalette);

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        overlay.classList.contains('open') ? closePalette() : openPalette();
      } else if (e.key === 'Escape' && overlay.classList.contains('open')) {
        closePalette();
      } else if (overlay.classList.contains('open') && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        const items = results.querySelectorAll('.cmdk-item');
        if (!items.length) return;
        items[activeIndex] && items[activeIndex].classList.remove('active');
        if (e.key === 'ArrowDown') activeIndex = (activeIndex + 1) % items.length;
        else activeIndex = (activeIndex - 1 + items.length) % items.length;
        items[activeIndex].classList.add('active');
        items[activeIndex].scrollIntoView({ block: 'nearest' });
      } else if (overlay.classList.contains('open') && e.key === 'Enter') {
        const items = results.querySelectorAll('.cmdk-item');
        if (activeIndex >= 0 && items[activeIndex]) {
          window.location.href = items[activeIndex].getAttribute('href');
        } else if (items.length) {
          window.location.href = items[0].getAttribute('href');
        }
      }
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closePalette();
    });

    input.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      const q = input.value.trim();
      debounceTimer = setTimeout(function () { fetchResults(q); }, 200);
    });
  });

  // ── CUSTOM CURSOR (desktop only) ──
  if (window.matchMedia('(pointer: coarse)').matches) return;

  document.body.style.cursor = 'none';

  const dot = document.getElementById('cursor-dot');
  const bracket = document.getElementById('cursor-bracket');
  const dataEl = document.getElementById('cursor-data');
  const valX = document.getElementById('val-x');
  const valY = document.getElementById('val-y');

  if (!dot) return;

  let mouseX = 0, mouseY = 0, dataX = 0, dataY = 0;

  function pad(n) { return String(Math.round(n)).padStart(4, '0'); }

  document.addEventListener('mousemove', function (e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.left = mouseX + 'px';
    dot.style.top = mouseY + 'px';
    bracket.style.left = mouseX + 'px';
    bracket.style.top = mouseY + 'px';
    valX.textContent = pad(mouseX);
    valY.textContent = pad(mouseY);
  });

  function lerp(a, b, t) { return a + (b - a) * t; }

  function animate() {
    dataX = lerp(dataX, mouseX, 0.15);
    dataY = lerp(dataY, mouseY, 0.15);
    dataEl.style.left = dataX + 'px';
    dataEl.style.top = dataY + 'px';
    requestAnimationFrame(animate);
  }
  animate();

  document.addEventListener('mouseleave', function () {
    dot.style.opacity = '0';
    dataEl.style.opacity = '0';
    bracket.style.opacity = '0';
  });

  document.addEventListener('mouseenter', function (e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.left = mouseX + 'px';
    dot.style.top = mouseY + 'px';
    bracket.style.left = mouseX + 'px';
    bracket.style.top = mouseY + 'px';
    dataX = mouseX;
    dataY = mouseY;
    dot.style.opacity = '1';
    dataEl.style.opacity = '1';
    bracket.style.opacity = '1';
  });

  document.addEventListener('mousedown', function () {
    dot.style.transform = 'translate(-50%, -50%) scale(2.5)';
  });

  document.addEventListener('mouseup', function () {
    dot.style.transform = 'translate(-50%, -50%) scale(1)';
  });

  document.querySelectorAll('a, button').forEach(function (el) {
    el.addEventListener('mouseenter', function () {
      dot.style.transform = 'translate(-50%, -50%) scale(2.5)';
      dot.style.background = '#34d399';
    });
    el.addEventListener('mouseleave', function () {
      dot.style.transform = 'translate(-50%, -50%) scale(1)';
      dot.style.background = '#059669';
    });
  });

})();
