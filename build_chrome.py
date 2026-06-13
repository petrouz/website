#!/usr/bin/env python3
import pathlib, re
SITE = pathlib.Path(__file__).resolve().parent
HEADER = (SITE / 'partials' / 'header.html').read_text(encoding='utf-8').strip()
FOOTER = (SITE / 'partials' / 'footer.html').read_text(encoding='utf-8').strip()
PAGES = ['index.html', 'why.html', 'features.html', 'install.html', 'legal.html', 'download/index.html']
PAGES += sorted(str(p.relative_to(SITE)) for p in (SITE / 'docs').glob('*.html'))
HDR = re.compile(r'<header\b.*?</header>', re.DOTALL)
FTR = re.compile(r'<footer\b.*?</footer>', re.DOTALL)
for rel in PAGES:
    p = SITE / rel
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    t, nh = HDR.subn(lambda m: HEADER, t, count=1)
    t, nf = FTR.subn(lambda m: FOOTER, t, count=1)
    p.write_text(t, encoding='utf-8')
    print(rel, 'header=' + str(nh), 'footer=' + str(nf))
