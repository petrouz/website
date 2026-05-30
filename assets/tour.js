// Auto-play product tour for the home page. Cross-fades through the
// captured MurOS pages inside a faux browser chrome, syncing the URL
// bar, caption and dots. Pauses on hover/focus and when the tab is
// hidden; fully static (first slide visible) under prefers-reduced-motion.
(function () {
  var root = document.querySelector('[data-tour]');
  if (!root) return;

  var slides = Array.prototype.slice.call(root.querySelectorAll('[data-slide]'));
  if (slides.length === 0) return;

  var urlEl = root.querySelector('[data-tour-url]');
  var titleEl = root.querySelector('[data-tour-title]');
  var descEl = root.querySelector('[data-tour-desc]');
  var progressEl = root.querySelector('[data-tour-progress]');
  var toggleBtn = root.querySelector('[data-tour-toggle]');
  var dots = Array.prototype.slice.call(root.querySelectorAll('[data-tour-dot]'));

  var DURATION = 4000; // ms per slide
  var current = 0;
  var paused = false;
  var startTs = 0;
  var raf = null;

  var reduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function show(i) {
    slides.forEach(function (s, idx) {
      var on = idx === i;
      s.classList.toggle('opacity-100', on);
      s.classList.toggle('opacity-0', !on);
      s.classList.toggle('pointer-events-none', !on);
      s.setAttribute('aria-hidden', on ? 'false' : 'true');
    });
    dots.forEach(function (d, idx) {
      var on = idx === i;
      d.classList.toggle('bg-amber-400', on);
      d.classList.toggle('bg-slate-300', !on);
      d.setAttribute('aria-current', on ? 'true' : 'false');
    });
    var s = slides[i];
    if (urlEl) urlEl.textContent = s.getAttribute('data-url') || '/';
    if (titleEl) titleEl.textContent = s.getAttribute('data-title') || '';
    if (descEl) descEl.textContent = s.getAttribute('data-desc') || '';
    current = i;
  }

  function go(delta) {
    show((current + delta + slides.length) % slides.length);
    startTs = 0; // reset timer for the new slide
  }

  function tick(ts) {
    if (paused) { raf = requestAnimationFrame(tick); return; }
    if (!startTs) startTs = ts;
    var elapsed = ts - startTs;
    var pct = Math.min(100, (elapsed / DURATION) * 100);
    if (progressEl) progressEl.style.width = pct + '%';
    if (elapsed >= DURATION) {
      startTs = ts;
      if (progressEl) progressEl.style.width = '0%';
      show((current + 1) % slides.length);
    }
    raf = requestAnimationFrame(tick);
  }

  function setPaused(p) {
    paused = p;
    if (toggleBtn) {
      toggleBtn.textContent = p ? '\u25B6' : '\u275A\u275A';
      toggleBtn.setAttribute('aria-label', p ? 'Play the tour' : 'Pause the tour');
    }
  }

  // Init
  show(0);

  if (reduced) {
    // Respect reduced motion: no autoplay, just the first frame plus
    // clickable dots for manual navigation.
    if (toggleBtn) toggleBtn.style.display = 'none';
    if (progressEl) progressEl.style.display = 'none';
    dots.forEach(function (d, idx) {
      d.addEventListener('click', function () { show(idx); });
    });
    return;
  }

  dots.forEach(function (d, idx) {
    d.addEventListener('click', function () { show(idx); startTs = 0; });
  });
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () { setPaused(!paused); });
  }
  root.addEventListener('mouseenter', function () { setPaused(true); });
  root.addEventListener('mouseleave', function () { setPaused(false); });
  root.addEventListener('focusin', function () { setPaused(true); });
  root.addEventListener('focusout', function () { setPaused(false); });
  document.addEventListener('visibilitychange', function () {
    setPaused(document.hidden);
  });

  raf = requestAnimationFrame(tick);
})();
