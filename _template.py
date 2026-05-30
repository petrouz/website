#!/usr/bin/env python3
"""Tiny page generator for the MurOS marketing site.

Reads a JSON spec from stdin and writes a complete HTML page under
site/. Wraps the body content with the shared header / footer. Keeps
the pages consistent without pulling in a static site generator.

Spec keys:
  page:        slug used to highlight the active nav link (features,
               install, download, hardware, docs)
  title:       <title> content
  description: <meta description>
  body:        the page body HTML (everything between <main> tags)
"""
from __future__ import annotations
import json, sys, pathlib

SITE = pathlib.Path(__file__).resolve().parent

# Sun / moon icons for the theme toggle (moon shown on light pages, sun on dark).
THEME_ICONS = ('<svg class="theme-icon-moon" width="16" height="16" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    '<svg class="theme-icon-sun" width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="4"/><path d="M12 2v1M12 21v1M4.22 4.22l.7.7M19.08 19.08l.7.7'
    'M2 12h1M21 12h1M4.22 19.78l.7-.7M19.08 4.92l.7-.7"/></svg>')

THEME_TOGGLE_DESKTOP = (f'<button type="button" data-theme-toggle aria-label="Switch theme" '
    f'title="Switch theme" class="theme-toggle inline-flex items-center justify-center w-8 h-8 '
    f'rounded border border-slate-300 text-slate-600 hover:text-slate-900 hover:bg-slate-50">'
    f'{THEME_ICONS}</button>')

THEME_TOGGLE_MOBILE = (f'<button type="button" data-theme-toggle class="theme-toggle flex '
    f'items-center gap-2 px-4 py-2 mt-1 text-left text-slate-600 hover:text-slate-900 '
    f'hover:bg-slate-50">{THEME_ICONS}<span>Dark mode</span></button>')

THEME_HEAD = ('<script>(function(){try{var t=localStorage.getItem("muros-theme");'
    'if(t==="dark"||(!t&&window.matchMedia("(prefers-color-scheme: dark)").matches)){'
    'document.documentElement.classList.add("dark");}}catch(e){}})();</script>')

NAV = [
    ('features', 'Features'),
    ('install',  'Install'),
    ('docs',     'Docs'),
]

def render(spec: dict) -> str:
    page = spec['page']
    # The same link set is rendered twice: once inline for sm+ screens
    # (hidden on mobile) and once stacked inside a <details> hamburger
    # for small viewports. Sharing the link list keeps the active-tab
    # underline consistent across both renderings.
    inline_links: list[str] = []
    mobile_links: list[str] = []
    for slug, label in NAV:
        target = 'docs/quickstart.html' if slug == 'docs' else f'{slug}.html'
        cls = 'nav-link hover:text-slate-900'
        if slug == page:
            cls += ' active'
        inline_links.append(f'<a href="{target}" class="{cls}">{label}</a>')
        mobile_links.append(
            f'<a href="{target}" class="{cls} px-4 py-2 hover:bg-slate-50">{label}</a>'
        )
    inline_nav = '\n      '.join(inline_links)
    mobile_nav = '\n        '.join(mobile_links)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0f172a">
<title>{spec["title"]}</title>
<meta name="description" content="{spec["description"]}">
<link rel="canonical" href="https://muros.org/{page}.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="MurOS">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="https://muros.org/{page}.html">
<meta property="og:title" content="{spec["title"]}">
<meta property="og:description" content="{spec["description"]}">
<meta property="og:image" content="https://muros.org/assets/og-cover.jpg">
<meta property="og:image:secure_url" content="https://muros.org/assets/og-cover.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="670">
<meta property="og:image:alt" content="MurOS - turn any Linux into a firewall">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{spec["title"]}">
<meta name="twitter:description" content="{spec["description"]}">
<meta name="twitter:image" content="https://muros.org/assets/og-cover.jpg">
<link rel="stylesheet" href="assets/app.css">
{THEME_HEAD}
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Organization","@id":"https://muros.org/#org","name":"MurOS","url":"https://muros.org/","logo":"https://muros.org/assets/logo-dark.svg","sameAs":["https://github.com/murosorg/muros"]}},
{{"@type":"WebSite","@id":"https://muros.org/#website","name":"MurOS","url":"https://muros.org/","publisher":{{"@id":"https://muros.org/#org"}}}}
]}}
</script>
</head>
<body class="bg-white text-slate-900 antialiased">

<header class="border-b border-slate-200">
  <div class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
    <a href="index.html" class="flex items-center gap-2 font-semibold text-slate-900">
      <span class="inline-block w-2 h-5 bg-amber-400"></span>
      <span>MurOS</span>
    </a>
    <nav class="hidden sm:flex items-center gap-6 text-sm text-slate-600">
      {inline_nav}
      <a href="https://github.com/murosorg/muros" class="text-slate-900 font-medium border border-slate-300 px-3 py-1 rounded hover:bg-slate-50">GitHub</a>
      {THEME_TOGGLE_DESKTOP}
    </nav>
    <details class="sm:hidden relative">
      <summary class="list-none cursor-pointer p-2 -mr-2 select-none" aria-label="Open menu">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="7" x2="21" y2="7"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="17" x2="21" y2="17"/></svg>
      </summary>
      <div class="absolute right-0 mt-2 bg-white border border-slate-200 rounded shadow-lg py-2 w-52 z-20 flex flex-col text-sm">
        {mobile_nav}
        <a href="https://github.com/murosorg/muros" class="px-4 py-2 mt-1 mx-3 text-slate-900 font-medium border border-slate-300 rounded text-center hover:bg-slate-50">GitHub</a>
        {THEME_TOGGLE_MOBILE}
      </div>
    </details>
  </div>
</header>

<main>
{spec["body"]}
</main>

<footer class="border-t border-slate-200 py-10 mt-16">
  <div class="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-slate-500">
    <div class="flex items-center gap-2">
      <span class="inline-block w-1.5 h-3 bg-amber-400"></span>
      <span>MurOS &middot; AGPL v3</span>
    </div>
    <div class="flex items-center gap-5">
      <a href="legal.html" class="hover:text-slate-900">Legal</a>
      <a href="https://github.com/murosorg/muros" class="hover:text-slate-900">GitHub</a>
      <a href="https://github.com/murosorg/muros/issues" class="hover:text-slate-900">Issues</a>
      <a href="https://github.com/murosorg/muros/blob/main/LICENSE" class="hover:text-slate-900">License</a>
    </div>
  </div>
</footer>

<script src="assets/version.js" defer></script>
<script src="assets/theme.js"></script>
</body>
</html>
'''

if __name__ == '__main__':
    spec = json.loads(sys.stdin.read())
    out = SITE / f'{spec["page"]}.html'
    out.write_text(render(spec))
    print(f'{out} : {len(out.read_text())} bytes')
