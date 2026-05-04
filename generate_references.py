"""
Regenerate references.bib from MyLibrary.bib.

Run manually or automatically via .latexmkrc before each bibtex call.
Scans all chapter .tex files for cite keys, extracts matching entries from
MyLibrary.bib, applies BibLaTeX->BibTeX conversion, and writes references.bib.
"""

import re
import glob
import sys

sys.path.insert(0, '.')
from convert_citations import extract_brace_content, clean_entry

CITE_RE = re.compile(r'\\cite[a-z]*\*?\{([^}]+)\}')
ENTRY_HEADER = re.compile(r'@\w+\{(\w[\w:.\-+]+),', re.MULTILINE)

# Manual patches for entries missing data in MyLibrary.bib.
# 'insert_fields' are added after the opening @type{key, line.
PATCHES = {}


def collect_cite_keys(tex_globs):
    keys = set()
    for pattern in tex_globs:
        for path in glob.glob(pattern):
            with open(path) as f:
                text = f.read()
            for m in CITE_RE.finditer(text):
                for k in m.group(1).split(','):
                    keys.add(k.strip())
    return keys


def apply_patch(entry, key):
    patch = PATCHES.get(key)
    if not patch:
        return entry
    for field, value in patch.get('insert_fields', []):
        if re.search(rf'\b{field}\s*=', entry):
            continue
        entry = re.sub(r'(\n)', rf'\n  {field} = {{{value}}},\1', entry, count=1)
    return entry


def generate(bib_path='MyLibrary.bib', out_path='references.bib',
             tex_globs=('ch*.tex', 'ch*/*.tex', 'ap*.tex')):
    import os
    if not os.path.exists(bib_path):
        print(f'  {bib_path} not found, skipping regeneration')
        return

    keys = collect_cite_keys(tex_globs)
    print(f'  {len(keys)} cite keys found in tex sources')

    with open(bib_path) as f:
        lib = f.read()

    written = set()
    parts = []
    for m in ENTRY_HEADER.finditer(lib):
        key = m.group(1)
        if key in written:
            continue
        brace_pos = lib.index('{', m.start())
        try:
            _, end = extract_brace_content(lib, brace_pos)
        except Exception:
            print(f'  WARNING: could not extract entry for key {key!r}')
            continue
        entry = clean_entry(lib[m.start():end])
        entry = apply_patch(entry, key)
        parts.append(entry)
        written.add(key)

    missing = keys - written
    if missing:
        print(f'  WARNING: keys not found in {bib_path}: {missing}')

    with open(out_path, 'w') as f:
        f.write('\n\n'.join(parts) + '\n')
    print(f'  Wrote {len(written)} entries to {out_path}')


if __name__ == '__main__':
    print(f'Generating references.bib from MyLibrary.bib...')
    generate()
