#!/usr/bin/env python3
# Stamp the app.css link in every built page with a short content hash so a
# stylesheet change is picked up immediately by browsers instead of serving a
# stale cached copy. Runs last in the build, after Tailwind has produced
# assets/app.css. Re-running is idempotent: an existing ?v= stamp is replaced.
import hashlib
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parent
CSS = SITE / 'assets' / 'app.css'
PAGES = ['index.html', 'why.html', 'features.html', 'install.html', 'legal.html', '404.html', 'download/index.html']
PAGES += sorted(str(p.relative_to(SITE)) for p in (SITE / 'docs').glob('*.html'))

digest = hashlib.sha256(CSS.read_bytes()).hexdigest()[:12]
link = re.compile(r'(href="/?assets/app\.css)(?:\?v=[0-9a-f]+)?(")')
for rel in PAGES:
    p = SITE / rel
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8')
    text, n = link.subn(lambda m: m.group(1) + '?v=' + digest + m.group(2), text)
    p.write_text(text, encoding='utf-8')
    print(rel, 'stamped=' + str(n))
