/*
 * Version display for the MurOS site.
 *
 * The authoritative version is the muros package currently published on
 * download.muros.org (the apt repository users actually install from). Its
 * Packages index is parsed for the "muros" stanza and the Version field is
 * written to every <span data-muros-tag> (prefixed with "v") and every
 * <span data-muros-version> (bare). This keeps the site in lockstep with the
 * download server instead of the GitHub release list.
 *
 * GitHub is still queried, best effort, only for the secondary release
 * history: the <span data-muros-date> month/year label and the optional
 * <div data-muros-recent-releases> table. Every call is a silent no-op on
 * failure so the page stays readable offline.
 */
(function () {
  var TAGS = document.querySelectorAll('[data-muros-tag]');
  var VERS = document.querySelectorAll('[data-muros-version]');
  var DATES = document.querySelectorAll('[data-muros-date]');
  var RECENT = document.querySelector('[data-muros-recent-releases]');

  // --- Primary source: the apt repository on download.muros.org ----------
  if (TAGS.length || VERS.length) {
    fetch('https://download.muros.org/dists/stable/main/binary-amd64/Packages', {
      headers: { 'Accept': 'text/plain' },
    })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(r.status); })
      .then(function (text) {
        // Packages is a list of stanzas separated by blank lines. Find the
        // one for the "muros" package and read its Version field.
        var stanzas = text.split(/\n\s*\n/);
        var version = null;
        for (var i = 0; i < stanzas.length; i++) {
          if (/^Package:\s*muros\s*$/m.test(stanzas[i])) {
            var m = stanzas[i].match(/^Version:\s*(.+?)\s*$/m);
            if (m) { version = m[1]; break; }
          }
        }
        if (!version) return;
        // Strip a Debian revision suffix (e.g. "0.9.51-1" -> "0.9.51").
        var bare = version.replace(/-\d+$/, '');
        TAGS.forEach(function (n) { n.textContent = 'v' + bare; });
        VERS.forEach(function (n) { n.textContent = bare; });
      })
      .catch(function () { /* keep the hardcoded fallback in the markup */ });
  }

  // --- Secondary: GitHub release history (dates + recent list) -----------
  if (!DATES.length && !RECENT) return;
  fetch('https://api.github.com/repos/murosorg/muros/releases?per_page=10', {
    headers: { 'Accept': 'application/vnd.github+json' },
  })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (list) {
      function parse(tag) {
        var s = String(tag || '').replace(/^v/, '');
        var m = s.match(/^(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$/);
        if (!m) return [-1];
        return [parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10),
                m[4] === undefined ? 1 : 0,
                m[4] === undefined ? 0 : parseInt(m[4], 10)];
      }
      function cmp(a, b) {
        for (var i = 0; i < Math.max(a.length, b.length); i++) {
          var x = a[i] || 0, y = b[i] || 0;
          if (x !== y) return x - y;
        }
        return 0;
      }
      var pick = null;
      for (var i = 0; i < list.length; i++) {
        var r = list[i];
        if (r.draft) continue;
        if (!pick || cmp(parse(r.tag_name), parse(pick.tag_name)) > 0) pick = r;
      }
      if (!pick) return;
      // Note: the tag/version spans are populated from download.muros.org
      // above. Here we only derive the publish date and recent list.
      var months = ['January','February','March','April','May','June',
                    'July','August','September','October','November','December'];
      if (pick.published_at) {
        var d = new Date(pick.published_at);
        var label = months[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
        DATES.forEach(function (n) { n.textContent = label; });
      } else {
        DATES.forEach(function (n) { n.textContent = ''; });
      }

      // Recent releases list. Renders the 6 highest semver tags as a
      // compact table with a link to each release on GitHub. The
      // container element is the optional <div data-muros-recent-releases>.
      var listHost = document.querySelector('[data-muros-recent-releases]');
      if (listHost) {
        var sorted = list.slice().filter(function (r) { return !r.draft; });
        sorted.sort(function (a, b) { return cmp(parse(b.tag_name), parse(a.tag_name)); });
        sorted = sorted.slice(0, 6);
        if (!sorted.length) {
          listHost.innerHTML = '<p class="text-sm text-slate-500">No release yet.</p>';
        } else {
          var html = '<table class="w-full text-sm border border-slate-200 rounded overflow-hidden">';
          html += '<thead class="bg-slate-50 text-slate-700"><tr>';
          html += '<th class="text-left font-medium px-3 py-2">Tag</th>';
          html += '<th class="text-left font-medium px-3 py-2 hidden sm:table-cell">Published</th>';
          html += '<th class="text-right font-medium px-3 py-2"></th></tr></thead><tbody>';
          sorted.forEach(function (r, i) {
            var d = r.published_at ? new Date(r.published_at) : null;
            var when = d ? (d.getUTCDate() + ' ' + months[d.getUTCMonth()] + ' ' + d.getUTCFullYear()) : '';
            var border = i === sorted.length - 1 ? '' : ' border-b border-slate-200';
            html += '<tr class="' + border + '">';
            html += '<td class="px-3 py-2 mono">' + r.tag_name + '</td>';
            html += '<td class="px-3 py-2 text-slate-500 hidden sm:table-cell">' + when + '</td>';
            html += '<td class="px-3 py-2 text-right"><a class="text-amber-700 hover:text-amber-800 font-medium" href="' + r.html_url + '" target="_blank" rel="noopener">View &rarr;</a></td>';
            html += '</tr>';
          });
          html += '</tbody></table>';
          listHost.innerHTML = html;
        }
      }
    })
    .catch(function () {
      DATES.forEach(function (n) { n.textContent = ''; });
      var listHost = document.querySelector('[data-muros-recent-releases]');
      if (listHost) {
        listHost.innerHTML = '<p class="text-sm text-slate-500">Unable to reach the GitHub API. See <a class="text-amber-700 hover:text-amber-800" href="https://github.com/murosorg/muros/releases">all releases on GitHub</a>.</p>';
      }
    });
})();
