#!/usr/bin/env python3
"""Pre-render the MurOS docs to static HTML for SEO.

Reads the markdown sources from the sibling muros repo (../muros/docs and
../muros/CHANGELOG.md, overridable with MUROS_REPO) and writes one static
page per doc under ./docs/, plus a docs.html landing index. Each page is
fully server-rendered with its own title, description, canonical and
structured data, so search engines index the content directly instead of
a client-side fetch.
"""
from __future__ import annotations
import datetime, html, json, os, pathlib, re, markdown

# Date the docs section first went live. Used as datePublished in the
# TechArticle structured data; dateModified tracks each source file.
DOCS_PUBLISHED = '2026-05-27'

SITE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ.get('MUROS_REPO', SITE.parent / 'muros'))
DOCS_SRC = REPO / 'docs'
OUT = SITE / 'docs'

# slug -> (title, description, source path relative to repo, github blob path)
DOCS = {
    'quickstart':   ('Quickstart', 'Install MurOS on Debian 13 and reach a working firewall in about fifteen minutes.', DOCS_SRC / 'quickstart.md', 'docs/quickstart.md'),
    'first-filter': ('First filter rule', 'Create your first stateful filter rule from the MurOS web UI.', DOCS_SRC / 'first-filter.md', 'docs/first-filter.md'),
    'concepts':     ('Concepts', 'Core MurOS concepts: zones, stage in database, apply, and automatic rollback.', DOCS_SRC / 'concepts.md', 'docs/concepts.md'),
    'architecture': ('Architecture', 'How MurOS is built: database model, boot sequence and kernel push.', DOCS_SRC / 'architecture.md', 'docs/architecture.md'),
    'ha':           ('High availability', 'Active/passive high availability with keepalived VRRP and conntrackd state sync.', DOCS_SRC / 'ha.md', 'docs/ha.md'),
    'hardware':     ('Hardware', 'Hardware sizing for MurOS: minimum specs, throughput brackets, recommended boxes and network cards.', DOCS_SRC / 'hardware.md', 'docs/hardware.md'),
    'changelog':    ('Changelog', 'Release history and notable changes in MurOS.', REPO / 'CHANGELOG.md', 'CHANGELOG.md'),
    'faq':          ('FAQ', 'Frequently asked questions and troubleshooting for MurOS.', DOCS_SRC / 'faq.md', 'docs/faq.md'),
}

# Sidebar grouping, in order.
GROUPS = [
    ('Getting started', ['quickstart', 'first-filter']),
    ('Reference', ['concepts', 'architecture', 'hardware', 'ha', 'changelog']),
    ('Help', ['faq']),
]

# Clicking "Docs" lands directly on the first documentation page (the docs
# layout with its sidebar), not on a separate landing index.
DOCS_HOME = '/docs/quickstart.html'

REPO_BLOB = 'https://github.com/murosorg/muros/blob/main/'
REPO_TREE = 'https://github.com/murosorg/muros/tree/main/'
HAMBURGER = ('<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="7" x2="21" '
    'y2="7"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="17" x2="21" '
    'y2="17"/></svg>')

# Sun / moon icons for the theme toggle. The CSS shows the icon matching the
# action a click would perform (moon on light pages, sun on dark pages).
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

# Sets the initial theme before first paint to avoid a flash. Reads the saved
# choice, falling back to the OS preference.
THEME_HEAD = ('<script>(function(){try{var t=localStorage.getItem("muros-theme");'
    'if(t==="dark"||(!t&&window.matchMedia("(prefers-color-scheme: dark)").matches)){'
    'document.documentElement.classList.add("dark");}}catch(e){}})();</script>')

NAV = [('why', 'Why MurOS'), ('features', 'Features'),
       ('docs', 'Docs')]


def header(active='docs'):
    inline, mobile = [], []
    for slug, label in NAV:
        cls = 'nav-link hover:text-slate-900' + (' active' if slug == active else '')
        # The Docs entry drops straight into the first doc page instead of a
        # separate landing index.
        href = DOCS_HOME if slug == 'docs' else f'/{slug}.html'
        inline.append(f'<a href="{href}" class="{cls}">{label}</a>')
        mobile.append(f'<a href="{href}" class="{cls} px-4 py-2 hover:bg-slate-50">{label}</a>')
    return f'''<header class="border-b border-slate-200">
  <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
    <a href="/index.html" class="flex items-center gap-2.5" aria-label="MurOS home">
      <img src="/assets/logo-dark.svg" alt="MurOS" class="block h-11 w-auto">
      <span class="mono text-base font-bold text-amber-700 -ml-2">[BETA]</span>
    </a>
    <nav class="hidden md:flex items-center gap-6 text-sm text-slate-600">
      {' '.join(inline)}
      <a href="/install.html" class="inline-flex items-center bg-amber-400 hover:bg-amber-500 text-slate-900 font-semibold px-3 py-1 rounded">Install</a>
      <a href="https://github.com/murosorg/muros" class="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-medium px-3 py-1 rounded"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" class="-ml-0.5"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a>
      {THEME_TOGGLE_DESKTOP}
    </nav>
    <details class="md:hidden relative"><summary class="list-none cursor-pointer p-2 -mr-2 select-none" aria-label="Open menu">{HAMBURGER}</summary><div class="absolute right-0 mt-2 bg-white border border-slate-200 rounded shadow-lg py-2 w-52 z-20 flex flex-col text-sm">
      {' '.join(mobile)}
      <a href="/install.html" class="px-4 py-2 mt-1 mx-3 bg-amber-400 hover:bg-amber-500 text-slate-900 font-semibold rounded text-center">Install</a>
      <a href="https://github.com/murosorg/muros" class="inline-flex items-center justify-center gap-1.5 px-4 py-2 mt-1 mx-3 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded text-center"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" class="-ml-0.5"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a>
      {THEME_TOGGLE_MOBILE}
    </div></details>
  </div>
</header>'''


FOOTER = '''<footer class="border-t border-slate-200">
  <div class="max-w-6xl mx-auto px-6 py-8 text-sm text-slate-500 flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
    <div class="flex items-center gap-4"><span>MurOS &middot; AGPL v3</span><span class="flex items-center gap-3"><a href="https://github.com/murosorg/muros" aria-label="GitHub" title="GitHub" class="hover:opacity-70" style="color:#181717"><svg width="26" height="26" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg></a><a href="https://www.linkedin.com/company/muros-firewall/" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn" class="hover:opacity-70" style="color:#0A66C2"><svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"/></svg></a></span></div>
    <div class="flex items-center gap-5">
      <a href="/features.html" class="hover:text-amber-700">Features</a>
      <a href="/install.html" class="hover:text-amber-700">Install</a>
      <a href="/docs/hardware.html" class="hover:text-amber-700">Hardware</a>
      <a href="/docs/quickstart.html" class="hover:text-amber-700">Docs</a>
    </div>
  </div>
</footer>'''


def sidebar(active):
    out = ['<aside class="doc-side lg:sticky lg:top-6 lg:self-start lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto">']
    for group, slugs in GROUPS:
        out.append(f'<div class="group-title">{group}</div>')
        for slug in slugs:
            title = DOCS[slug][0]
            cls = 'active' if slug == active else ''
            out.append(f'<a href="/docs/{slug}.html" class="{cls}">{title}</a>')
    out.append('<div class="group-title">Help</div>')
    out.append('<a href="https://github.com/murosorg/muros/issues">Issues (GitHub)</a>')
    out.append('<a href="https://github.com/murosorg/muros/discussions">Discussions</a>')
    out.append('</aside>')
    return '\n      '.join(out)


def shell(title, desc, canonical, jsonld, body):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0f172a">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="manifest" href="/site.webmanifest">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/app.css">
{THEME_HEAD}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="MurOS">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://muros.org/assets/og-cover.jpg">
<meta property="og:image:secure_url" content="https://muros.org/assets/og-cover.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="670">
<meta property="og:image:alt" content="MurOS - turn Linux into a firewall">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://muros.org/assets/og-cover.jpg">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body class="bg-white text-slate-900 antialiased">
<a href="#main" class="skip-link">Skip to content</a>

{header()}

<main id="main" tabindex="-1">
{body}
</main>

{FOOTER}

<script src="/assets/theme.js"></script>
</body>
</html>
'''


def _inline_plain(text: str) -> str:
    """Reduce a markdown line to readable plain text for structured data."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links -> label
    text = text.replace('`', '')                          # inline code ticks
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)         # bold
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)  # italic
    text = re.sub(r'^[-*]\s+', '', text)                   # list bullet
    return text.strip()


def faq_entries(md: str):
    """Yield (question, answer) pairs from a FAQ markdown document.

    Each level-two heading is a question; the answer is the prose under
    it, with fenced code blocks and headings dropped so the structured
    data stays short and readable.
    """
    entries, question, lines, in_code = [], None, [], False
    def flush():
        if question:
            answer = ' '.join(p for p in (_inline_plain(l) for l in lines) if p)
            answer = re.sub(r'\s+', ' ', answer).strip()
            if answer:
                entries.append((question, answer))
    for raw in md.splitlines():
        if raw.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        if raw.startswith('## '):
            flush()
            question, lines = raw[3:].strip(), []
        elif question is not None and not raw.startswith('#'):
            lines.append(raw)
    flush()
    return entries


def rewrite_repo_links(html_str):
    # Markdown sources link relative to the muros repo (e.g. README.md, docs/).
    # Those paths would 404 on the site, so point them at GitHub instead.
    def repl(m):
        url = m.group(1)
        if url.startswith(('http://', 'https://', '/', '#', 'mailto:')):
            return m.group(0)
        base = REPO_TREE if url.endswith('/') else REPO_BLOB
        return f'href="{base}{url}"'
    return re.sub(r'href="([^"]+)"', repl, html_str)


def render_doc(slug):
    title, desc, src, blob = DOCS[slug]
    md = src.read_text(encoding='utf-8')
    body_html = markdown.markdown(md, extensions=['fenced_code', 'tables', 'sane_lists', 'toc', 'attr_list'])
    body_html = rewrite_repo_links(body_html)
    canonical = f'https://muros.org/docs/{slug}.html'
    page_title = f'{title} - MurOS Docs'
    modified = datetime.date.fromtimestamp(src.stat().st_mtime).isoformat()
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'TechArticle', 'headline': title, 'description': desc, 'url': canonical,
         'inLanguage': 'en', 'author': {'@type': 'Organization', 'name': 'MurOS', 'url': 'https://muros.org/'},
         'publisher': {'@type': 'Organization', 'name': 'MurOS', 'url': 'https://muros.org/'},
         'datePublished': DOCS_PUBLISHED, 'dateModified': modified},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': 'https://muros.org/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Docs', 'item': 'https://muros.org' + DOCS_HOME},
            {'@type': 'ListItem', 'position': 3, 'name': title, 'item': canonical}]}]}
    if slug == 'faq':
        graph['@graph'].append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q,
             'acceptedAnswer': {'@type': 'Answer', 'text': a}}
            for q, a in faq_entries(md)]})
    jsonld = json.dumps(graph, indent=2)
    crumb = f'<a href="/index.html" class="hover:text-slate-900">~</a> / <a href="{DOCS_HOME}" class="hover:text-slate-900">docs</a> / <span class="text-slate-700">{slug}.md</span>'
    body = f'''<section>
  <div class="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-[14rem_1fr] gap-8">
      {sidebar(slug)}
    <article>
      <nav class="text-xs text-slate-500 mb-4 mono">{crumb}</nav>
      <div class="doc-prose">
{body_html}
      </div>
      <div class="mt-12 pt-6 border-t border-slate-200 text-sm text-slate-500 flex items-center justify-between">
        <a href="{REPO_BLOB}{blob}" class="hover:text-amber-700" target="_blank" rel="noopener">Edit this page on GitHub</a>
        <span class="mono text-xs">muros/docs</span>
      </div>
    </article>
  </div>
</section>'''
    (OUT / f'{slug}.html').write_text(shell(page_title, desc, canonical, jsonld, body), encoding='utf-8')


def render_landing():
    # No separate docs landing: /docs.html redirects to the first doc page so
    # any old link or bookmark drops straight into the docs layout.
    redirect = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Docs - MurOS</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://muros.org{DOCS_HOME}">
<meta http-equiv="refresh" content="0; url={DOCS_HOME}">
<script>location.replace('{DOCS_HOME}' + location.hash);</script>
</head>
<body>
<p>The documentation has moved to <a href="{DOCS_HOME}">{DOCS_HOME}</a>.</p>
</body>
</html>
'''
    (SITE / 'docs.html').write_text(redirect, encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True)
    for slug in DOCS:
        render_doc(slug)
    render_landing()
    print('docs:', ', '.join(sorted(DOCS)))
    print('wrote', len(DOCS), 'pages +', OUT / '..' , 'docs.html landing')


if __name__ == '__main__':
    main()
