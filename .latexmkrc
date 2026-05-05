# Regenerate references.bib from MyLibrary.bib before each bibtex run.
# Exit code 1 = bibtex warnings only; treat as success so latexmk completes.
$bibtex = 'python3 generate_references.py && (bibtex %O %B; ec=$?; test $ec -le 1)';
