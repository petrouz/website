// MurOS site theme handling.
//
// The site follows the operating system colour scheme; there is no manual
// toggle. The inline snippet in each page <head> sets the initial `dark` class
// on <html> before first paint (no flash). This script keeps the logo variant
// in sync and re-applies the resolved theme when the OS preference changes.
(function () {
  var root = document.documentElement;
  var mq = window.matchMedia('(prefers-color-scheme: dark)');

  function isDark() {
    return root.classList.contains('dark');
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

  function apply(dark) {
    root.classList.toggle('dark', dark);
    syncLogos();
  }

  // Re-assert the resolved theme on load: the inline head snippet can evaluate
  // matchMedia before the OS colour-scheme signal is ready (race seen on some
  // Linux/Chromium setups), leaving a dark-OS visitor on the light theme.
  apply(mq.matches);

  // Follow the OS theme as it changes.
  mq.addEventListener('change', function (e) {
    apply(e.matches);
  });
})();
