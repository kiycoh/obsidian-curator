---
name: obsidian-curator
description: "Curation & Restructure Pipeline — splits monolithic notes into atomic Hub-and-Spoke networks, and restructures/enriches lean, empty, or poorly formatted notes (especially YAML tags) using Obsidian Flavored Markdown (OFM) styling guidelines."
---

# Obsidian Curator — Curation Pipeline

The Curation pipeline operates in two modes depending on the condition of the target note:
1. **Decouple Mode (Decomposition)**: Applied to monolithic notes. Splits the monolith into an index-based Hub note and multiple atomic Spoke notes (target ~40 lines).
2. **Reformat & Enrich Mode (Restructuring)**: Applied to notes that are empty, too lean (< 600 characters), or badly formatted (especially YAML frontmatter tags). Re-styles the note, corrects metadata schemas, and enriches content with authoritative definitions.

## Inputs

- `<TARGET_NOTE>` — path to the note to refactor or reformat/enrich.
- `<PARENT_FOLDER>` — parent folder where the new notes/re-formatted note will reside.
- `<HUB_NAME>` — the primary Hub note that this note should link back to.

## Required Tools

This skill requires:
- **`web_search` & `web_extract`** (native tools or programmatically imported via `hermes_tools`) to locate authoritative definitions, formulas, and academic context.
- **`write_file` & `patch`** (native file operation tools) to commit updates to the vault.

## Differences from obsidian-injector

### In Decouple Mode:
- **Phase 1**: Parse the monolith's headings as candidate concepts (skip `find` step).
- **Phase 2**: Router maps concepts. The monolith itself matches the H1 title (which becomes the Hub).
- **Phase 3**: Write Spokes first (atomically, with `[[Hub title]]` link), then overwrite the Hub note with the Spoke index.

### In Reformat & Enrich Mode:
- **Phase 1**: Inspect the note's frontmatter and body. Check if the note is empty or contains **fewer than 600 characters** (< 600 chars).
- **Phase 2**: Check for missing context, empty bodies, and badly formatted YAML tags (e.g. camelCase, uppercase, spaces, or missing values).
- **Phase 3**: Reformat the YAML frontmatter (lowercase, hyphen-separated tags). If the content is too lean or empty, perform `web_search`/`web_extract` to retrieve factual, academic definitions and write a formal Italian body. Overwrite the target note with the polished, enriched version.

## Content Preservation & Deletion Rules

- **Enrichment Trigger**: Any note containing **fewer than 600 characters** (< 600 chars) must be actively enriched and restructured.
- **Anti-Deletion Policy**: Deleting existing information is **strictly discouraged** unless:
  1. The information is pure semantic/formatting noise.
  2. The model is rewriting/expanding that same concept in a more thorough, detailed, and academically rigorous manner.
  3. The model has verified via `web_search` that the original phrase, definition, or formula is factually incorrect.

## Hub/Target Note Rewrite Constraint

Hub rewrites use full `write_file`, never `patch`. This is the one case
where the Router overwrites existing content. The original monolith body
is preserved in the Spokes; only the Hub structure changes.

## External Enrichment (Optional)

If a concept within the target note is underspecified or requires formal formulas, standard academic definitions, or illustrative examples to be fully usable:
- **Do** leverage the native `web_search` and `web_extract` tools to retrieve authoritative reference materials.
- **Do not** introduce speculative or unverified claims. Ensure all fetched information is factually accurate, structured for academic readability, and integrated cleanly into the Spoke's Italian body text.

---

## Obsidian Flavored Markdown (OFM) Styling Instructions

Notes must be created and edited using valid Obsidian Flavored Markdown. This section outlines the structural syntax extensions to be utilized:

### 1. Frontmatter & Properties (YAML)
Every note must start with a YAML frontmatter block containing key metadata properties.
- **`tags`**: Note tags (always lowercase and hyphen-separated, e.g. `machine-learning`).
- **`aliases`**: Alternative names for the note.
- **`cssclasses`**: Style classes if needed.
See [PROPERTIES.md](references/PROPERTIES.md) for full types and details.

### 2. Internal Links (Wikilinks)
Use `[[wikilinks]]` for internal notes.
```markdown
[[Note Name]]                          Link to note
[[Note Name|Display Text]]             Custom display text
[[Note Name#Heading]]                  Link to heading
[[Note Name#^block-id]]                Link to block
```

### 3. Embeds
Prefix any wikilink with `!` to embed its content inline:
```markdown
![[Note Name]]                         Embed full note
![[Note Name#Heading]]                 Embed section
![[image.png]]                         Embed image
```
See [EMBEDS.md](references/EMBEDS.md) for PDF, audio, and query embeds.

### 4. Callouts
Use callouts for structured callouts and tips:
```markdown
> [!note]
> Basic callout.

> [!tip] Scholarly Tip
> Helpful hint or context.
```
Common types: `note`, `tip`, `warning`, `info`, `example`, `quote`, `bug`, `danger`, `question`.
See [CALLOUTS.md](references/CALLOUTS.md) for details on folding and type lists.

### 5. Math (LaTeX)
Use LaTeX math blocks for equations:
```markdown
Inline: $e^{i\pi} + 1 = 0$

Block:
$$
\frac{a}{b} = c
$$
```

### 6. Diagrams (Mermaid)
Use Mermaid code blocks for rendering relationships:
```mermaid
graph TD
    A[Start] --> B[Process]
```

---

## Pitfalls

- **Spoke linkback** — every Spoke must contain `[[Hub Title]]` in the
  body (not frontmatter). The Phase 3 validator enforces this.
- **No orphans** — never create a Spoke without updating the Hub's index.
  Order operations: write all Spokes first, then rewrite the Hub last with
  the complete Spoke list.
- **Atomicity** — if a Spoke would exceed 40 lines, split further (sub-Spoke
  or sub-section). Do not loosen the limit.
