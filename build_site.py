from pathlib import Path
import re
root = Path(__file__).parent
header = (root / 'partials/header.html').read_text()
footer = (root / 'partials/footer.html').read_text()
for page in root.rglob('*.html'):
    if 'partials' in page.parts:
        continue
    content = page.read_text()
    current = page.relative_to(root).as_posix()
    rendered = header
    if current == 'index.html':
        rendered = rendered.replace('href="https://muros.org/" class="nav-link hover:text-slate-900"', 'href="https://muros.org/" class="nav-link hover:text-slate-900 active"', 1)
    elif current.startswith('docs/'):
        rendered = rendered.replace('href="https://muros.org/docs/quickstart.html" class="nav-link hover:text-slate-900"', 'href="https://muros.org/docs/quickstart.html" class="nav-link hover:text-slate-900 active"', 1)
    elif current == 'why.html':
        rendered = rendered.replace('href="https://muros.org/why.html" class="nav-link hover:text-slate-900"', 'href="https://muros.org/why.html" class="nav-link hover:text-slate-900 active"', 1)
    content = re.sub(r'<header\b.*?</header>', rendered, content, count=1, flags=re.S)
    content = re.sub(r'<footer\b.*?</footer>', footer, content, count=1, flags=re.S)
    page.write_text(content)
