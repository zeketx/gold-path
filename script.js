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

  // 5. Audit request form -> mailto:audit@goldpath.example
  const form = document.getElementById('audit-form');
  if (form) {
    const nameInput = document.getElementById('f-name');
    const emailInput = document.getElementById('f-email');
    const stackInput = document.getElementById('f-stack');
    const changeInput = document.getElementById('f-change');
    const errName = document.getElementById('err-name');
    const errEmail = document.getElementById('err-email');
    const statusEl = document.getElementById('form-status');

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      errName.textContent = '';
      errEmail.textContent = '';
      statusEl.textContent = '';

      let valid = true;
      const name = nameInput.value.trim();
      const email = emailInput.value.trim();

      if (!name) {
        errName.textContent = 'Enter your name.';
        valid = false;
      }

      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errEmail.textContent = 'Enter a valid work email address.';
        valid = false;
      }

      if (!valid) {
        if (!name) nameInput.focus();
        else emailInput.focus();
        return;
      }

      const stack = stackInput.value;
      const change = changeInput.value.trim() || 'Not specified';
      const subject = `Free 20-call audit request — ${name} (${stack})`;
      const body = [
        `Name: ${name}`,
        `Work email: ${email}`,
        `Agent platform: ${stack}`,
        `What we are testing or changing: ${change}`
      ].join('\n');

      const mailtoUrl = `mailto:audit@goldpath.example?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      statusEl.textContent = 'Opening your email client to send a draft to audit@goldpath.example (placeholder inbox).';
      window.location.href = mailtoUrl;
    });
  }
})();
