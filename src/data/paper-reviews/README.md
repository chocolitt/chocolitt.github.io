# Editing the paper-review archive

The source for `/published-paper-reviews.html` is organized by paper and panel. The Astro endpoint assembles these files during development and builds; there is no generated HTML file to edit or keep in sync.

## Edit a paper

Each paper has its own directory:

```text
p01/
  erratum.html
  review.html
  audit.html
```

Edit the relevant panel directly. These are HTML fragments, so ordinary paragraphs use `<p>...</p>`, lists use `<ol>` or `<ul>`, and tables retain the existing table markup. Keep TeX between `$...$`, `\(...\)`, or `\[...\]`; MathJax renders it on the page.

Paper titles, summary counts, confidence totals, severity flags, and badges live in `papers.json`. The order of that list controls both the sidebar and the paper cards.

For coauthored work, keep the per-paper `disclosure` field in `papers.json`. It is rendered inside that paper's expanded card so the AI-generation and non-endorsement notice remains attached to each set of materials.

## Edit the page itself

`page.html` contains the introduction, overall audit, styles, and browser behavior. Leave these assembly markers in place:

```text
{{PAPER_NAVIGATION}}
{{PAPER_COUNT}}
{{PAPER_CARDS}}
```

The paper count is automatic. Collection-wide metrics and audit tables in `page.html` are editorial figures, so update them manually when the underlying totals change.

## Preview

Double-click `Preview Website.command` at the repository root. It builds this page from the source files and runs all validation checks before opening the local site.
