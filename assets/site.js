/* NoteToMail — shared marketing page behaviour (no dependencies) */
(function () {
  'use strict';

  // ── Mobile menu ──
  var burger = document.querySelector('.hamburger');
  var mobile = document.getElementById('mobileMenu');
  if (burger && mobile) {
    burger.addEventListener('click', function () {
      var open = mobile.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    mobile.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        mobile.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      }
    });
  }

  // ── Nav dropdowns (click + keyboard, hover on pointer devices) ──
  var dropdowns = [].slice.call(document.querySelectorAll('.nav-item-dd'));

  function closeAll(except) {
    dropdowns.forEach(function (dd) {
      if (dd === except) return;
      dd.setAttribute('data-open', 'false');
      var t = dd.querySelector('.nav-trigger');
      if (t) t.setAttribute('aria-expanded', 'false');
    });
  }

  dropdowns.forEach(function (dd) {
    var trigger = dd.querySelector('.nav-trigger');
    if (!trigger) return;

    trigger.addEventListener('click', function () {
      var open = dd.getAttribute('data-open') === 'true';
      closeAll(dd);
      dd.setAttribute('data-open', open ? 'false' : 'true');
      trigger.setAttribute('aria-expanded', open ? 'false' : 'true');
    });

    dd.addEventListener('mouseenter', function () {
      if (window.matchMedia('(hover: hover)').matches) {
        closeAll(dd);
        dd.setAttribute('data-open', 'true');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
    dd.addEventListener('mouseleave', function () {
      if (window.matchMedia('(hover: hover)').matches) {
        dd.setAttribute('data-open', 'false');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });

    dd.addEventListener('focusout', function (e) {
      if (!dd.contains(e.relatedTarget)) {
        dd.setAttribute('data-open', 'false');
        trigger.setAttribute('aria-expanded', 'false');
      }
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll(null);
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav-item-dd')) closeAll(null);
  });

  // ── FAQ accordion ──
  [].slice.call(document.querySelectorAll('.faq-q')).forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.parentElement;
      var wasOpen = item.classList.contains('open');
      [].slice.call(document.querySelectorAll('.faq-item')).forEach(function (i) {
        i.classList.remove('open');
        var q = i.querySelector('.faq-q');
        if (q) q.setAttribute('aria-expanded', 'false');
      });
      if (!wasOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  // ── Scroll reveal ──
  var els = [].slice.call(document.querySelectorAll('.fade-up'));
  if (!('IntersectionObserver' in window) ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    els.forEach(function (el) { el.classList.add('visible'); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  els.forEach(function (el) { observer.observe(el); });
})();
