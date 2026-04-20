# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a LaTeX dissertation template for UNC (University of North Carolina) graduate school requirements. It was used successfully for a dissertation approved in 2019 and is intended as an evolving resource for future PhD students.

## Building

Compile the full dissertation PDF:
```bash
pdflatex diss.tex
bibtex diss
pdflatex diss.tex
pdflatex diss.tex
```

Or with latexmk (handles multiple passes automatically):
```bash
latexmk -pdf diss.tex
```

Clean build artifacts:
```bash
latexmk -c
```

## Document Structure

`diss.tex` is the root file. It inputs everything in order:

1. `common/preamble.tex` — all `\usepackage` declarations and inputs `common/layout.tex` and `common/macros.tex`
2. `frontmatter/pages.tex` — orchestrates all front matter pages (title, copyright, abstract, TOC, lists of tables/figures/abbreviations)
3. `ch1.tex`, `ch2.tex`, `ch3.tex` — chapter files (add more by inserting `\input{chN}` in `diss.tex`)
4. `ap1.tex`, `ap2.tex` — appendix files (after `\appendix` declaration in `diss.tex`)
5. `common/references.tex` — bibliography using `\bibliographystyle{apsr}` and `\bibliography{diss}`

All bibliography entries go in `diss.bib`.

## Key Configuration Files

- **`common/layout.tex`** — margins (1.25" left/right, 1" top/bottom), double-spacing, chapter/section heading formats, paragraph indent (4ex), footnote sizing
- **`common/macros.tex`** — custom theorem environments and utility commands
- **`common/preamble.tex`** — all package imports; citation style uses `harvard` package (not natbib); theorems use `ntheorem` (not amsthm)

## Custom Macros (`common/macros.tex`)

- `\hyp` — numbered Hypothesis theorem environment
- `\prop` — numbered Proposition theorem environment
- `\subhyp` — sub-hypothesis environment (generates H1a, H1b, etc.)
- `\normhyp` — resets hypothesis counter back to normal numbering after `subhyp`
- `\yncomment{text}` — renders blue bracketed comment in PDF (for advisor/collaborator notes); `YN` initials are hardcoded
- `\rightparend{text}` — flushes text to right end of paragraph (used for QED-style endings)

## Adding a New Chapter

1. Create `chN.tex` starting with `\chapter{Title}`
2. Add `\input{chN}` in `diss.tex` after the last chapter input

## UNC Formatting Notes

- Front matter uses 2" top margins; body chapters use ~1.62" (achieved via `\titlespacing` offset of 0.62in)
- Appendix chapter headings reset to 1" top margin via `\titlespacing{\chapter}{0in}{-.38in}{11pt}` in `diss.tex`
- Chapter headings are formatted as "CHAPTER N: TITLE" (all caps, same line, normal font size)
- Graduate school requirements change yearly — verify current specs before submission

# Rules

- Only edit formatting, never edit prose unless specifically prompted. Always ask for verification before editing prose.
