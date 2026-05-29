// Lightbox - tiny vanilla JS modal for screenshots.
// Wires up any <a data-lightbox href="image.png"> to open the linked
// image centered on top of a dimmed backdrop. Click outside the image
// or press ESC to close. Stays on the current page (no new tab, no
// browser back/forward).
(function () {
  function ensureRoot() {
    if (document.getElementById('lightbox-root')) return;
    var root = document.createElement('div');
    root.id = 'lightbox-root';
    root.className = 'fixed inset-0 z-50 bg-slate-900/85 ' +
      'items-center justify-center p-6 lg:p-12 cursor-zoom-out hidden';
    root.style.display = 'none';
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.innerHTML =
      '<img id="lightbox-img" alt="" ' +
      'class="block max-h-full max-w-full rounded shadow-2xl cursor-default" ' +
      'onclick="event.stopPropagation()">';
    document.body.appendChild(root);
    root.addEventListener('click', close);
  }
  function open(href) {
    ensureRoot();
    var root = document.getElementById('lightbox-root');
    var img = document.getElementById('lightbox-img');
    img.src = href;
    root.classList.remove('hidden');
    root.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
  function close() {
    var root = document.getElementById('lightbox-root');
    if (!root) return;
    root.classList.add('hidden');
    root.style.display = 'none';
    document.body.style.overflow = '';
    document.getElementById('lightbox-img').src = '';
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-lightbox]');
    if (!a) return;
    e.preventDefault();
    open(a.getAttribute('href'));
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });
})();
