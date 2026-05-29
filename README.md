# MurOS marketing site

Static marketing site for [muros.org](https://muros.org).

Plain HTML pages styled with Tailwind CSS. The pages are committed as
static files; the stylesheet is compiled once with the Tailwind CLI into
`assets/app.css` (no runtime CDN, no client-side build).

## Layout

- `index.html`, `features.html`, `install.html`, `download.html`,
  `hardware.html`, `docs.html` - the pages
- `assets/` - compiled CSS (`app.css`), scripts, images, screenshots
- `src/input.css` - Tailwind entry point and custom CSS
- `tailwind.config.js` - scans `*.html` and `assets/*.js` for classes
- `robots.txt`, `sitemap.xml` - SEO
- `_template.py` - shared header/footer renderer

## Build the CSS

```sh
npm install
npm run build:css      # one-off build -> assets/app.css
npm run watch:css      # rebuild on change while editing
```

Note: this machine has npm set to omit dev dependencies. If `npm install`
skips Tailwind, run `npm install --production=false`.

## Hosting

Served by nginx on the OVH VPS that backs `muros.org`, from
`/opt/muros/site`, over HTTPS (Let's Encrypt). HTTP redirects to HTTPS.

## Deploy

```sh
./deploy.sh
```

This compiles the CSS, then rsyncs the static files to `/opt/muros/site`
on the server. nginx serves the files directly, so no restart is needed.
