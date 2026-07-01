(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {

    // ── NAV TOGGLE ──
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle) {
      toggle.addEventListener('click', function () {
        links.classList.toggle('open');
      });
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
      dot.style.background = '#9333ea';
    });
    el.addEventListener('mouseleave', function () {
      dot.style.transform = 'translate(-50%, -50%) scale(1)';
      dot.style.background = '#7c3aed';
    });
  });

})();
