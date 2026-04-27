"""
One-time script: convert SciWheel \href citations in ch3/main.tex to \cite{}.

Steps:
  1. Parse ch3/ch3_refs.tex  → {sciwheel_id: doi}
  2. Parse MyLibrary.bib     → {doi: cite_key}
  3. Merge                   → {sciwheel_id: cite_key}
  4. Replace \href citations in ch3/main.tex with \cite{}
  5. Extract referenced bib entries into ch3/ch3.bib
  6. Update common/references.tex to include ch3/ch3
"""

import re
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_brace_content(text, start):
    """Return the content inside the outermost {} starting at `start` (which
    must point to the opening '{').  Returns (content, end_index)."""
    assert text[start] == '{', f"Expected '{{' at position {start}"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    raise ValueError("Unmatched brace starting at position {start}")


def normalize_doi(doi):
    return doi.strip().lower().rstrip('.')


# ---------------------------------------------------------------------------
# Step 1: ch3/ch3_refs.tex → {sciwheel_id: doi}
# ---------------------------------------------------------------------------

def parse_refs(path='ch3/ch3_refs.tex'):
    with open(path) as f:
        text = f.read()

    sciwheel_doi = {}
    doi_pattern = re.compile(r'10\.\d{4,}/\S+')
    bib_url = re.compile(r'\\href\{https://sciwheel\.com/work/bibliography/(\d+)\}\{')

    for m in bib_url.finditer(text):
        sid = m.group(1)
        brace_start = m.end() - 1          # position of the opening '{'
        content, _ = extract_brace_content(text, brace_start)
        dois = doi_pattern.findall(content)
        if dois:
            raw = dois[-1]                  # DOI is at the end of the entry
            doi = normalize_doi(raw.rstrip('}'))
            sciwheel_doi[sid] = doi
        else:
            sciwheel_doi[sid] = None        # no DOI found

    return sciwheel_doi


# ---------------------------------------------------------------------------
# Step 2: MyLibrary.bib → {doi: cite_key}
# ---------------------------------------------------------------------------

def has_suffix(key):
    """Return True if cite key ends with a trailing letter like 2020a."""
    return bool(re.search(r'\d[a-z]$', key))


def parse_bib(path='MyLibrary.bib'):
    with open(path) as f:
        text = f.read()

    doi_citekey = {}
    entry_header = re.compile(r'@\w+\{(\w[\w:.\-+]+),', re.MULTILINE)

    for m in entry_header.finditer(text):
        key = m.group(1)
        # Extract body up to the matching closing brace of the entry
        brace_pos = text.index('{', m.start())
        try:
            body, _ = extract_brace_content(text, brace_pos)
        except (ValueError, AssertionError):
            continue
        doi_m = re.search(r'doi\s*=\s*\{([^}]+)\}', body, re.IGNORECASE)
        if not doi_m:
            continue
        doi = normalize_doi(doi_m.group(1))
        if doi not in doi_citekey:
            doi_citekey[doi] = key
        else:
            existing = doi_citekey[doi]
            # Prefer the base key (no trailing letter suffix)
            if has_suffix(existing) and not has_suffix(key):
                doi_citekey[doi] = key

    return doi_citekey


# ---------------------------------------------------------------------------
# Step 3: Build {sciwheel_id: cite_key}
# ---------------------------------------------------------------------------

def build_lookup(sciwheel_doi, doi_citekey):
    lookup = {}
    missing_doi = []
    missing_key = []
    for sid, doi in sciwheel_doi.items():
        if doi is None:
            missing_doi.append(sid)
        elif doi in doi_citekey:
            lookup[sid] = doi_citekey[doi]
        else:
            missing_key.append((sid, doi))
    return lookup, missing_doi, missing_key


# ---------------------------------------------------------------------------
# Step 4: Replace \href citations in ch3/main.tex
# ---------------------------------------------------------------------------

CITATION_RE = re.compile(
    r'\\href\{https://sciwheel\.com/work/citation\?ids=([\d,]+)[^}]*\}'
    r'\{\\textsuperscript\{[^}]+\}\}'
)

# Reversed format: \textsuperscript{\href{...?ids=ID...}{N,}\href{...}{N}}
REVERSED_CITATION_RE = re.compile(
    r'\\textsuperscript\{'
    r'(?:\\href\{https://sciwheel\.com/work/citation\?ids=(\d+)[^}]*\}\{[^}]*\})+'
    r'\}'
)

SINGLE_ID_RE = re.compile(r'sciwheel\.com/work/citation\?ids=(\d+)')


def replace_citations(path, lookup):
    with open(path) as f:
        text = f.read()

    used_keys = set()
    unchanged = []

    def replacer(m):
        ids = [s.strip() for s in m.group(1).split(',')]
        keys = []
        for id_ in ids:
            if id_ in lookup:
                keys.append(lookup[id_])
                used_keys.add(lookup[id_])
            else:
                unchanged.append(id_)
                return m.group(0)          # leave unchanged
        return r'\cite{' + ', '.join(keys) + '}'

    def reversed_replacer(m):
        ids = SINGLE_ID_RE.findall(m.group(0))
        keys = []
        for id_ in ids:
            if id_ in lookup:
                keys.append(lookup[id_])
                used_keys.add(lookup[id_])
            else:
                unchanged.append(id_)
                return m.group(0)
        return r'\cite{' + ', '.join(keys) + '}'

    new_text = CITATION_RE.sub(replacer, text)
    new_text = REVERSED_CITATION_RE.sub(reversed_replacer, new_text)

    with open(path, 'w') as f:
        f.write(new_text)

    return used_keys, unchanged


# ---------------------------------------------------------------------------
# Step 5: Extract referenced bib entries into ch3/ch3.bib
# ---------------------------------------------------------------------------

NAME_PART_RE = re.compile(
    r'family=([^,}]+),\s*given=([^,}]+)'
    r'(?:,\s*prefix=([^,}]+),\s*useprefix=(true|false))?'
)


def convert_name_part(m):
    """Convert BibLaTeX extended name part to traditional BibTeX."""
    family = m.group(1).strip()
    given = m.group(2).strip()
    prefix = m.group(3)
    useprefix = m.group(4)
    if prefix and useprefix == 'true':
        return f'{{{prefix} {family}}}, {given}'
    elif prefix:
        return f'{{{prefix} {family}}}, {given}'
    return f'{family}, {given}'


STRIP_FIELDS = {'abstract', 'file', 'keywords', 'urldate', 'langid',
                'pmcid', 'pmid', 'annotation', 'note', 'shortjournal',
                'shorttitle', 'eprinttype', 'eprintclass', 'pubstate',
                'eventtitle', 'isbn', 'issn'}

UNICODE_SUBS = [
    ('β', r'$\beta$'),
    ('α', r'$\alpha$'),
    ('γ', r'$\gamma$'),
    ('δ', r'$\delta$'),
    ('μ', r'$\mu$'),
]


def strip_fields(entry):
    """Remove BibTeX fields listed in STRIP_FIELDS."""
    lines = entry.split('\n')
    out = []
    skip = False
    depth = 0
    for line in lines:
        stripped = line.strip()
        # Detect start of a field to strip
        if not skip:
            field_m = re.match(r'(\w+)\s*=\s*\{', stripped)
            if field_m and field_m.group(1).lower() in STRIP_FIELDS:
                skip = True
                depth = stripped.count('{') - stripped.count('}')
                if depth == 0:
                    skip = False
                continue
        if skip:
            if stripped in ('}', ''):
                out.append(line)
                skip = False
                continue
            depth += stripped.count('{') - stripped.count('}')
            if depth <= 0:
                skip = False
            continue
        out.append(line)
    return '\n'.join(out)


def clean_entry(entry):
    """Convert BibLaTeX-only constructs to traditional BibTeX."""
    # @online / @dataset / @unpublished -> @misc
    entry = re.sub(r'^@(online|dataset|unpublished)\{', '@misc{', entry, flags=re.MULTILINE)
    # BibLaTeX journaltitle -> journal
    entry = re.sub(r'\bjournaltitle\s*=', 'journal =', entry)
    # BibLaTeX date = {YYYY-MM-DD} -> year = {YYYY} (only if no year field present)
    if not re.search(r'\byear\s*=', entry, re.IGNORECASE):
        entry = re.sub(r'\bdate\s*=\s*\{(\d{4})[^}]*\}', r'year = {\1}', entry)
    else:
        entry = re.sub(r'\bdate\s*=\s*\{[^}]*\},?\n?', '', entry)
    # Convert extended author name parts
    # Only apply inside the author = {...} field
    def fix_author_field(m):
        return 'author = {' + NAME_PART_RE.sub(convert_name_part, m.group(1)) + '}'
    entry = re.sub(r'author\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
                   fix_author_field, entry, flags=re.DOTALL)
    # Strip verbose/problematic fields
    entry = strip_fields(entry)
    # Substitute Unicode math symbols
    for uni, latex in UNICODE_SUBS:
        entry = entry.replace(uni, latex)
    return entry


def extract_bib_entries(bib_path, keys, out_path):
    import os
    with open(bib_path) as f:
        text = f.read()

    entry_header = re.compile(r'@\w+\{(\w[\w:.\-+]+),', re.MULTILINE)

    # Collect keys already present in out_path so we don't duplicate them
    already_written = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            existing = f.read()
        for m in entry_header.finditer(existing):
            already_written.add(m.group(1))

    written_keys = set(already_written)
    output_parts = []

    for m in entry_header.finditer(text):
        key = m.group(1)
        if key not in keys or key in written_keys:
            continue
        brace_pos = text.index('{', m.start())
        try:
            _, end = extract_brace_content(text, brace_pos)
        except (ValueError, AssertionError):
            print(f"  WARNING: could not extract entry for key '{key}'")
            continue
        entry = clean_entry(text[m.start():end])
        output_parts.append(entry)
        written_keys.add(key)

    if output_parts:
        with open(out_path, 'a') as f:
            f.write('\n\n' + '\n\n'.join(output_parts) + '\n')

    new_keys = written_keys - already_written
    return list(new_keys), keys - written_keys


# ---------------------------------------------------------------------------
# Step 6: Update common/references.tex
# ---------------------------------------------------------------------------

def update_references_tex(path='common/references.tex'):
    with open(path) as f:
        text = f.read()
    new = r'\bibliography{diss,ch2/references,ch3/ch3}'
    if new in text:
        print(f"  Already up to date.")
        return
    old = r'\bibliography{diss,ch2/references}'
    if old not in text:
        print(f"  WARNING: expected '{old}' not found in {path} — skipping update")
        return
    with open(path, 'w') as f:
        f.write(text.replace(old, new, 1))
    print(f"  Updated {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=== Step 1: Parsing ch3/ch3_refs.tex ===")
    sciwheel_doi = parse_refs()
    has_doi = sum(1 for v in sciwheel_doi.values() if v)
    print(f"  {len(sciwheel_doi)} entries, {has_doi} with DOI")

    print("\n=== Step 2: Parsing MyLibrary.bib ===")
    doi_citekey = parse_bib()
    print(f"  {len(doi_citekey)} unique DOIs with cite keys")

    print("\n=== Step 3: Building sciwheel_id → cite_key lookup ===")
    lookup, missing_doi, missing_key = build_lookup(sciwheel_doi, doi_citekey)
    print(f"  Mapped: {len(lookup)}")
    if missing_doi:
        print(f"  No DOI in ch3_refs.tex ({len(missing_doi)}): {missing_doi}")
    if missing_key:
        print(f"  DOI not in MyLibrary.bib ({len(missing_key)}):")
        for sid, doi in missing_key:
            print(f"    sciwheel {sid}: {doi}")

    print("\n=== Step 4: Replacing citations in ch3/main.tex ===")
    used_keys, unchanged = replace_citations('ch3/main.tex', lookup)
    print(f"  Cite keys used: {len(used_keys)}")
    if unchanged:
        print(f"  Unchanged (no mapping) sciwheel IDs: {unchanged}")

    remaining = len(re.findall(r'sciwheel\.com/work/citation', open('ch3/main.tex').read()))
    print(f"  Remaining sciwheel citation \href tags: {remaining}")

    print("\n=== Step 5: Writing ch3/ch3.bib ===")
    written, not_found = extract_bib_entries('MyLibrary.bib', used_keys, 'ch3/ch3.bib')
    print(f"  Wrote {len(written)} entries to ch3/ch3.bib")
    if not_found:
        print(f"  WARNING: could not find bib entries for: {not_found}")

    print("\n=== Step 6: Updating common/references.tex ===")
    update_references_tex()

    print("\nDone. Run: pdflatex diss.tex && bibtex diss && pdflatex diss.tex && pdflatex diss.tex")
