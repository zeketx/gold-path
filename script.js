(function () {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 1. Hero entrance once on load
  const hero = document.querySelector('[data-enter]');
  if (hero) {
    if (reducedMotion) {
      hero.classList.add('is-entered');
    } else {
      requestAnimationFrame(() => {
        hero.classList.add('is-entered');
      });
    }
  }

  // 2. Mobile menu toggle
  const menuBtn = document.querySelector('.menu-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  if (menuBtn && mobileNav) {
    menuBtn.addEventListener('click', () => {
      const expanded = menuBtn.getAttribute('aria-expanded') === 'true';
      menuBtn.setAttribute('aria-expanded', String(!expanded));
      mobileNav.hidden = expanded;
    });

    mobileNav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        menuBtn.setAttribute('aria-expanded', 'false');
        mobileNav.hidden = true;
      });
    });
  }

  // 3. Dealt moment: scroll-driven word-highlight in #why-independent
  const highlightEl = document.querySelector('[data-word-highlight]');
  if (highlightEl && !reducedMotion) {
    const words = highlightEl.textContent.trim().split(/\s+/);
    highlightEl.textContent = '';
    const spans = words.map((word, idx) => {
      const span = document.createElement('span');
      span.className = 'wh-word';
      span.textContent = idx === words.length - 1 ? word : word + ' ';
      highlightEl.appendChild(span);
      return span;
    });

    const updateHighlight = () => {
      const rect = highlightEl.getBoundingClientRect();
      const vh = window.innerHeight || 800;
      const start = vh * 0.88;
      const end = vh * 0.28;
      const progress = Math.min(1, Math.max(0, (start - rect.top) / (start - end)));
      const litCount = Math.round(progress * spans.length);
      spans.forEach((span, i) => {
        span.classList.toggle('is-lit', i < litCount);
      });
    };

    updateHighlight();
    window.addEventListener('scroll', updateHighlight, { passive: true });
    window.addEventListener('resize', updateHighlight, { passive: true });
  }

  // 4. Scenario tabs (manual click only — no timed tabs)
  const tabButtons = document.querySelectorAll('.scenario-btn[role="tab"]');
  const tabPanels = document.querySelectorAll('.scenario-panel[role="tabpanel"]');
  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('aria-controls');
      tabButtons.forEach((b) => {
        const active = b === btn;
        b.classList.toggle('is-active', active);
        b.setAttribute('aria-selected', String(active));
      });
      tabPanels.forEach((panel) => {
        panel.hidden = panel.id !== targetId;
      });
    });
  });

  // 5. Audit request form -> Netlify Forms (AJAX, inline thank-you)
  const form = document.getElementById('audit-form');
  const thanksEl = document.getElementById('audit-thanks');
  if (form) {
    const nameInput = document.getElementById('f-name');
    const emailInput = document.getElementById('f-email');
    const platformInput = document.getElementById('f-platform');
    const errName = document.getElementById('err-name');
    const errEmail = document.getElementById('err-email');
    const errPlatform = document.getElementById('err-platform');
    const statusEl = document.getElementById('form-status');
    const submitBtn = form.querySelector('button[type="submit"]');

    const encode = (data) =>
      new URLSearchParams(data).toString();

    const showThanks = () => {
      form.classList.add('is-hidden');
      if (thanksEl) {
        thanksEl.hidden = false;
        thanksEl.setAttribute('tabindex', '-1');
        thanksEl.focus();
      }
    };

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      errName.textContent = '';
      errEmail.textContent = '';
      if (errPlatform) errPlatform.textContent = '';
      if (statusEl) statusEl.textContent = '';

      let valid = true;
      const name = nameInput.value.trim();
      const email = emailInput.value.trim();
      const platform = platformInput ? platformInput.value : '';

      if (!name) {
        errName.textContent = 'Enter your name.';
        valid = false;
      }

      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errEmail.textContent = 'Enter a valid work email address.';
        valid = false;
      }

      if (platformInput && !platform) {
        if (errPlatform) errPlatform.textContent = 'Select a platform.';
        valid = false;
      }

      if (!valid) {
        if (!name) nameInput.focus();
        else if (!email || errEmail.textContent) emailInput.focus();
        else if (platformInput) platformInput.focus();
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending…';
      }

      const payload = new FormData(form);

      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: encode(payload)
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error('Request failed');
          }
          showThanks();
        })
        .catch(() => {
          if (statusEl) {
            statusEl.textContent = 'We could not send the form from this page. Try again, or use the thank-you page path.';
          }
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Book a free 20-call audit';
          }
        });
    });
  }
})();
