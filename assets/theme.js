// MurOS site theme handling.
//
// The inline snippet in each page <head> sets the initial `dark` class on
// <html> before first paint (no flash). This script wires the toggle
// buttons, keeps the logo variant in sync, and keeps following the system
// preference until the visitor makes an explicit choice.
(function () {
  var root = document.documentElement;
  var KEY = 'muros-theme';
  var mq = window.matchMedia('(prefers-color-scheme: dark)');

  function isDark() {
    return root.classList.contains('dark');
  }

  function stored() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  // The wordmark ships in two files: logo-dark.svg (dark ink, light pages)
  // and logo.svg (white ink, dark pages). Swap whichever is in the DOM.
  function syncLogos() {
    var dark = isDark();
    var imgs = document.querySelectorAll('img[alt="MurOS"]');
    for (var i = 0; i < imgs.length; i++) {
      var src = imgs[i].getAttribute('src') || '';
      var next = dark
        ? src.replace('logo-dark.svg', 'logo.svg')
        : src.replace(/logo(?!-dark)\.svg/, 'logo-dark.svg');
      if (next !== src) {
        imgs[i].setAttribute('src', next);
      }
    }
  }

  function apply(dark, persist) {
    root.classList.toggle('dark', dark);
    if (persist) {
      try {
        localStorage.setItem(KEY, dark ? 'dark' : 'light');
      } catch (e) {}
    }
    syncLogos();
  }

  // Re-assert the resolved theme on load. The inline head snippet can
  // evaluate matchMedia before the OS color-scheme signal is ready (race
  // observed on some Linux/Chromium setups), which leaves a dark-OS visitor
  // on the light theme. Recompute here once matchMedia is reliable.
  if (!stored()) {
    apply(mq.matches, false);
  } else {
    syncLogos();
  }

  // Follow the OS theme while the visitor has not chosen one explicitly.
  mq.addEventListener('change', function (e) {
    if (!stored()) {
      apply(e.matches, false);
    }
  });

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-theme-toggle]');
    if (btn) {
      apply(!isDark(), true);
    }
  });
})();
