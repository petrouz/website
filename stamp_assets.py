#!/usr/bin/env python3
# Stamp cacheable asset references in every built page with a short content
# hash so a change is picked up immediately by browsers instead of serving a
# stale cached copy (nginx sets "expires max" on css/js). Runs last in the
# build, after Tailwind has produced assets/app.css. Re-running is idempotent:
# an existing ?v= stamp is replaced.
import hashlib
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parent
PAGES = ['index.html', 'why.html', 'features.html', 'install.html', 'legal.html', '404.html', 'download/index.html']
PAGES += sorted(str(p.relative_to(SITE)) for p in (SITE / 'docs').glob('*.html'))

# Each asset is referenced from the page root with an optional leading slash.
ASSETS = [
    ('href', 'assets/app.css'),
    ('src', 'assets/version.js'),
]

stamps = []
for attr, rel_asset in ASSETS:
    f = SITE / rel_asset
    if not f.exists():
        continue
    digest = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
    pattern = re.compile(
        r'(' + attr + r'="/?' + re.escape(rel_asset) + r')(?:\?v=[0-9a-f]+)?(")')
    stamps.append((rel_asset, pattern, digest))

for rel in PAGES:
    p = SITE / rel
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8')
    total = 0
    for rel_asset, pattern, digest in stamps:
        text, n = pattern.subn(
            lambda m: m.group(1) + '?v=' + digest + m.group(2), text)
        total += n
    p.write_text(text, encoding='utf-8')
    print(rel, 'stamped=' + str(total))
