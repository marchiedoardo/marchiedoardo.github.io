#!/usr/bin/env python3
"""Render publications.bib into publications.html (and a short list on index.html).

Usage, from the repository root:
    python3 tools/build_publications.py

No third-party packages are needed. The script replaces only the text between
the marker comments, so the rest of each page stays as you wrote it:

    publications.html   <!-- PUBLICATIONS:START ... -->  ...  <!-- PUBLICATIONS:END -->
    index.html          <!-- RECENT:START ... -->        ...  <!-- RECENT:END -->

Supported BibTeX fields
    title, author, year, month, journal / booktitle / school / publisher / howpublished,
    volume, number, pages, doi, url, eprint (arXiv id), note
Optional extra fields, shown as links:
    pdf, code, data, slides     (a URL or a site path such as files/paper.pdf)
Optional flags:
    preprint = {true}           tag the entry as a preprint (entries with
                                bioRxiv / arXiv / medRxiv in the venue, and
                                @unpublished entries, are tagged automatically)
    selected = {true}           prefer this entry in the short list on index.html

Equal contribution: put an asterisk after the surname, e.g.
    author = {Rossi*, Mario and Bianchi*, Anna and ...}

Limitations (deliberate, to stay dependency-free):
    @string macros and string concatenation with # are not expanded.
    Only common LaTeX accents and symbols are converted; check the output once.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration: edit these.
# ---------------------------------------------------------------------------

# How your name appears in author lists, as (surname, first initial).
# Add one tuple per spelling you have published under.
MY_NAMES = [("Name", "Y")]

# Number of entries shown under "Recent publications" on the home page.
RECENT_COUNT = 3

# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

PREPRINT_SERVERS = ("biorxiv", "arxiv", "medrxiv", "chemrxiv", "research square", "ssrn")


# ---------- BibTeX parsing ----------

def _read_delimited(text: str, i: int) -> tuple[str, int]:
    """Read a {...} or "..." value starting at text[i]; return (content, next index)."""
    if text[i] == "{":
        depth, j = 1, i + 1
        while j < len(text) and depth:
            if text[j] == "\\":
                j += 2
                continue
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        if depth:
            raise ValueError("unbalanced braces")
        return text[i + 1:j - 1], j
    if text[i] == '"':
        depth, j = 0, i + 1
        while j < len(text):
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == '"' and depth == 0:
                return text[i + 1:j], j + 1
            j += 1
        raise ValueError("unterminated quoted value")
    m = re.compile(r"[^,}\s]+").match(text, i)  # bare value, e.g. year = 2024
    return m.group(0), m.end()


def parse_bibtex(text: str) -> list[dict]:
    entries = []
    for m in re.finditer(r"@(\w+)\s*([{(])", text):
        etype = m.group(1).lower()
        if etype in ("comment", "string", "preamble"):
            continue
        i = m.end()
        try:
            key_end = text.index(",", i)
        except ValueError:
            continue
        entry = {"ENTRYTYPE": etype, "ID": text[i:key_end].strip()}
        i = key_end + 1
        while True:
            fm = re.compile(r"\s*([\w\-:]+)\s*=\s*").match(text, i)
            if not fm:
                break
            name = fm.group(1).lower()
            try:
                value, i = _read_delimited(text, fm.end())
            except ValueError as err:
                sys.exit(f"Could not parse field '{name}' in entry '{entry['ID']}': {err}")
            entry[name] = " ".join(value.split())
            sep = re.compile(r"\s*,?").match(text, i)
            i = sep.end()
        entries.append(entry)
    return entries


# ---------- LaTeX to text ----------

ACCENTS = {
    "'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303",
    "=": "\u0304", ".": "\u0307", "u": "\u0306", "v": "\u030c", "H": "\u030b",
    "c": "\u0327", "k": "\u0328", "r": "\u030a",
}
SYMBOLS = {
    r"\ss": "ß", r"\o": "ø", r"\O": "Ø", r"\ae": "æ", r"\AE": "Æ", r"\aa": "å",
    r"\AA": "Å", r"\l": "ł", r"\L": "Ł", r"\i": "ı", r"\&": "&", r"\%": "%",
    r"\$": "$", r"\_": "_", r"\#": "#",
}


GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "kappa": "κ", "lambda": "λ", "mu": "μ", "pi": "π", "rho": "ρ", "sigma": "σ",
    "tau": "τ", "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Delta": "Δ", "Gamma": "Γ", "Omega": "Ω",
}


def latex_to_text(s: str) -> str:
    import unicodedata

    def accent(m):
        cmd, letter = m.group(1), m.group(2)
        if letter in (r"\i", r"{\i}"):
            letter = "i"
        letter = letter.strip("{}")
        return unicodedata.normalize("NFC", letter + ACCENTS[cmd])

    # \'e, \'{e}, {\'e}, \c{c}, \v{s} ...
    s = re.sub(r"\\([\'`^\"~=.])\s*(\{\\i\}|\\i|\{?\w\}?)", accent, s)
    s = re.sub(r"\\([uvHckr])\s*(\{\\i\}|\\i|\{\w\})", accent, s)
    s = re.sub(r"\\([uvHckr]) (\w)", accent, s)
    for k in sorted(SYMBOLS, key=len, reverse=True):
        # word commands such as \ss swallow one following space; \& does not
        tail = r"(?![A-Za-z])\s?" if k[-1].isalpha() else ""
        s = re.sub(re.escape(k) + tail, lambda _m, v=SYMBOLS[k]: v, s)
    s = re.sub(r"\\(" + "|".join(GREEK) + r")(?![A-Za-z])\s?", lambda m: GREEK[m.group(1)], s)
    s = re.sub(r"\\(?:textit|emph|textbf|textrm|mathrm|text)\s*\{([^{}]*)\}", r"\1", s)
    s = s.replace("---", "\u2014").replace("--", "\u2013").replace("~", "\u00a0")
    s = re.sub(r"\$([^$]*)\$", r"\1", s)  # inline math: keep the content
    s = s.replace("{", "").replace("}", "")
    return " ".join(s.split())


# ---------- Formatting ----------

def split_authors(field: str) -> list[str]:
    return [a.strip() for a in re.split(r"\s+and\s+", field) if a.strip()]


def format_author(raw: str) -> str:
    """'Rossi, Mario Luigi' or 'Mario Luigi Rossi' -> 'M. L. Rossi' (HTML-escaped)."""
    raw = latex_to_text(raw)
    star = "*" if "*" in raw else ""
    raw = raw.replace("*", "").strip()
    if raw.lower() == "others":
        return "et al."
    if "," in raw:
        last, first = [p.strip() for p in raw.split(",", 1)]
    else:
        parts = raw.split()
        last, first = parts[-1], " ".join(parts[:-1])
    initials = " ".join(
        "-".join(p[0] + "." for p in w.split("-") if p) for w in first.split()
    )
    name = f"{initials} {last}".strip()
    is_me = any(
        last.lower() == s.lower() and (not first or first[0].upper() == i.upper())
        for s, i in MY_NAMES
    )
    text = html.escape(name) + star
    return f'<span class="me">{text}</span>' if is_me else text


def is_preprint(e: dict) -> bool:
    if e.get("preprint", "").lower() in ("true", "yes", "1"):
        return True
    if e["ENTRYTYPE"] == "unpublished":
        return True
    venue = (e.get("journal", "") + " " + e.get("publisher", "") + " " + e.get("howpublished", "")).lower()
    return any(p in venue for p in PREPRINT_SERVERS)


def link(href: str, label: str) -> str:
    return f'<a href="{html.escape(href, quote=True)}">{label}</a>'


def format_entry(e: dict, indent: str) -> str:
    title = html.escape(latex_to_text(e.get("title", "Untitled")).rstrip("."))
    authors = [format_author(a) for a in split_authors(e.get("author", ""))]
    venue = latex_to_text(e.get("journal") or e.get("booktitle") or e.get("howpublished")
                          or e.get("school") or e.get("institution") or e.get("publisher") or "")
    details = []
    if e.get("volume"):
        details.append(e["volume"] + (f"({e['number']})" if e.get("number") else ""))
    if e.get("pages"):
        details.append(latex_to_text(e["pages"]))
    venue_html = html.escape(venue)
    if details:
        venue_html += " " + html.escape(", ".join(details))
    if e.get("note"):
        note = html.escape(latex_to_text(e["note"]))
        venue_html = f"{venue_html}. {note}" if venue_html else note
    if is_preprint(e):
        venue_html += '<span class="tag">preprint</span>'

    links = []
    if e.get("doi"):
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", e["doi"])
        links.append(link(f"https://doi.org/{doi}", "DOI"))
    if e.get("eprint") and e.get("archiveprefix", "arxiv").lower() == "arxiv":
        links.append(link(f"https://arxiv.org/abs/{e['eprint']}", "arXiv"))
    for field, label in (("pdf", "PDF"), ("code", "Code"), ("data", "Data"), ("slides", "Slides")):
        if e.get(field):
            links.append(link(e[field], label))
    if e.get("url") and not e.get("doi"):
        links.append(link(e["url"], "Link"))

    out = [f"{indent}<li>",
           f'{indent}  <span class="pub-title">{title}</span>',
           f'{indent}  <span class="pub-authors">{", ".join(authors)}</span>',
           f'{indent}  <span class="pub-venue">{venue_html}</span>']
    if links:
        out.append(f'{indent}  <span class="pub-links">{" ".join(links)}</span>')
    out.append(f"{indent}</li>")
    return "\n".join(out)


def sort_key(e: dict):
    year = int(re.sub(r"\D", "", e.get("year", "0")) or 0)
    month = e.get("month", "").lower()[:3]
    month = MONTHS.get(month, int(month) if month.isdigit() else 0)
    return (year, month)


def render_full(entries: list[dict]) -> str:
    by_year: dict[str, list[dict]] = {}
    for e in entries:
        by_year.setdefault(e.get("year", "Undated"), []).append(e)
    lines = ['    <dl class="dated">']
    for year, items in by_year.items():
        lines.append(f"      <dt>{html.escape(year)}</dt>")
        lines.append('      <dd>\n        <ul class="pubs">')
        lines += [format_entry(e, "          ") for e in items]
        lines.append("        </ul>\n      </dd>")
    lines.append("    </dl>")
    return "\n".join(lines)


def render_recent(entries: list[dict]) -> str:
    selected = [e for e in entries if e.get("selected", "").lower() in ("true", "yes", "1")]
    rest = [e for e in entries if e not in selected]
    picks = (selected + rest)[:RECENT_COUNT]
    picks.sort(key=sort_key, reverse=True)
    return "\n".join(['      <ul class="pubs">'] + [format_entry(e, "        ") for e in picks] + ["      </ul>"])


def replace_block(path: Path, marker: str, content: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"(<!-- {marker}:START.*?-->)(.*?)(\s*<!-- {marker}:END -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"Markers <!-- {marker}:START --> / <!-- {marker}:END --> not found in {path.name}")
    text = pattern.sub(lambda m: m.group(1) + "\n" + content + m.group(3), text, count=1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bib", type=Path, default=ROOT / "publications.bib")
    ap.add_argument("--no-recent", action="store_true", help="do not update index.html")
    args = ap.parse_args()

    entries = parse_bibtex(args.bib.read_text(encoding="utf-8"))
    if not entries:
        sys.exit(f"No entries found in {args.bib}")
    entries.sort(key=sort_key, reverse=True)  # stable: file order kept within a month

    replace_block(ROOT / "publications.html", "PUBLICATIONS", render_full(entries))
    if not args.no_recent:
        replace_block(ROOT / "index.html", "RECENT", render_recent(entries))

    mine = sum('class="me"' in format_entry(e, "") for e in entries)
    print(f"Rendered {len(entries)} entries ({mine} with your name highlighted).")
    if mine < len(entries):
        print("Check MY_NAMES at the top of this script if your name is missing from some entries.")


if __name__ == "__main__":
    main()
