# Personal academic website

A static site for GitHub Pages: plain HTML and one CSS file.
There is no build step and no framework.
The site loads nothing from third parties (no web fonts, no analytics, no cookies).

## Files

| Path | Content |
|---|---|
| `index.html` | Home: name, role, short bio, links, research interests, recent papers |
| `research.html` | Research overview and one section per project or theme |
| `publications.html` | Full publication list, generated from `publications.bib` |
| `cv.html` | CV summary and a link to the full PDF |
| `404.html` | Page shown for any missing address |
| `assets/style.css` | All styling. Colours and fonts are tokens at the top. |
| `assets/` | Logo mark (`favicon.svg`), portrait and figure placeholders |
| `files/` | Put `cv.pdf` and any paper PDFs here |
| `publications.bib` | Your BibTeX. The current entries are fake placeholders. |
| `tools/build_publications.py` | Renders the BibTeX into the two pages above |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |

## 1. Fill in the placeholders

Every placeholder is wrapped in `<span class="ph">…</span>`.
It shows with a pink highlight so you can spot what is left.

- Find them all: `grep -n 'class="ph"' *.html`
- Replace the text and remove the `<span class="ph">` wrapper.
- Also edit the `<title>` and `<meta name="description">` in the head of each page.
  The same header is repeated in all five pages. Change it in each one.
- Replace `assets/portrait.svg` with your photo (4:5 ratio, about 880 × 1100 px, JPEG).
  Update the `src` in `index.html`.
- Replace `assets/figure-placeholder.svg` with real figures (SVG or PNG).
  Write a real `alt` text for each image.
- Put your CV at `files/cv.pdf`.

## 2. Publications

1. Replace the entries in `publications.bib` with your own.
   Google Scholar, ORCID, Zotero and journal pages all export BibTeX.
2. Edit `MY_NAMES` at the top of `tools/build_publications.py`,
   so the script can highlight your name.
3. Run, from the repository root:

   ```
   python3 tools/build_publications.py
   ```

The script rewrites only the text between the `PUBLICATIONS` markers in
`publications.html` and the `RECENT` markers in `index.html`.
It needs no packages. The docstring at the top lists the supported fields.
Extra fields such as `pdf`, `code` and `data` become links.
Add `selected = {true}` to an entry to show it on the home page.

## 3. Preview locally

Open `index.html` in a browser, or run a local server:

```
python3 -m http.server 8000
```

Then open <http://localhost:8000>.
The local server does not serve `404.html` for missing pages. GitHub Pages does.

## 4. Publish on GitHub Pages

1. Create a public repository named `<your-username>.github.io`.
2. Push these files to the `main` branch, at the repository root.
3. In the repository, open **Settings → Pages**.
   Set **Source** to *Deploy from a branch*, branch `main`, folder `/ (root)`.
4. After a minute, the site is live at `https://<your-username>.github.io`.

## 5. Connect your own domain

Follow this order. GitHub recommends it to stop someone else from claiming your domain.

1. **Verify the domain** in your *account* settings:
   **Settings → Pages → Add a domain**. GitHub gives you a TXT record to add at your registrar.
2. **Add the domain to the repository:** **Settings → Pages → Custom domain**.
   GitHub then commits a `CNAME` file to the repository. Keep it.
3. **Set the DNS records** at your registrar. Delete the registrar's default parking records first.

   | Type | Name | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `<your-username>.github.io` |

4. **Check** with `dig yourdomain.com +noall +answer`. Propagation can take up to 24 hours.
5. **Tick "Enforce HTTPS"** in **Settings → Pages**. It can take up to 24 hours to become available.

Do not add wildcard DNS records (`*`).

## Privacy checklist

- **Commit email.** Every commit in a public repository shows the author email.
  In GitHub **Settings → Emails**, enable *Keep my email addresses private*
  and *Block command line pushes that expose my email*.
  Then set the no-reply address in this repository:
  `git config user.email "<id>+<username>@users.noreply.github.com"`
  (GitHub shows the exact address on that settings page.)
- **Photo metadata.** Phone photos can carry GPS coordinates.
  Strip them before you commit: `exiftool -all= photo.jpg`, or export a fresh copy from an image editor.
- **PDF metadata.** Check the author and file-path fields of PDFs you upload:
  `exiftool files/cv.pdf`.
- **Email address on the page.** Any visible address gets scraped for spam.
  An institutional address or a dedicated alias limits the impact.
- **Domain registration.** Use a registrar that redacts WHOIS data by default.
- **Third-party content.** The site makes no external requests now.
  Embedding YouTube, Google Fonts, analytics or similar would change that.
- **Hosting logs.** GitHub, as the host, processes visitor IP addresses.
  For a site run from Germany, check whether you need an Impressum (§ 5 DDG)
  and a privacy notice. Many academic sites include both. Your institute's
  web or legal office can tell you what applies to you.

## Changing the look

- Colours: edit the tokens at the top of `assets/style.css`.
  Dark mode follows the visitor's system setting and has its own token block.
- Fonts: the site uses fonts already on the visitor's device (Charter or a similar serif for text,
  the system sans-serif for navigation). To use a web font, self-host the font files in `assets/`
  rather than loading them from Google, to keep the no-third-party property.
- Remove the pink placeholder highlight by deleting the `.ph` rule once all placeholders are gone.
