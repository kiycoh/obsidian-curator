---
name: obsidian-injector
description: "Inject Pipeline — ingests source markdown from an inbox into the Obsidian vault. Performs mechanical recon via execute_code, reasoning in-context, and file writes directly from the Router."
---

# Obsidian Injector — Inject Pipeline

## Curation Standards
The curation process must adhere strictly to these principles:
- **Factual Density**: Extract all concrete details, definitions, schemas, and examples from the source files. Avoid generalizations or hand-wavy summaries.
- **Modular Atomicity**: Avoid monolithic files. Split information into specific, granular concepts (Spoke notes) of roughly ~40 lines to ensure high-resolution modularity.
- **YAML Frontmatter**: Maintain consistent tagging style: lowercase, hyphen-separated tags describing the semantic areas (e.g. `intelligenza-artificiale`, `machine-learning`, `reti-neurali`).
- **Scholarly Readability**: Write in formal Italian, using bold keywords, clear structures, lists, and callout blocks (`> [!TIP]`) to make content highly usable for scholars and researchers.
- **Content Preservation Guardrail**: Deleting entire notes, sentences, or words without a logical and heavily weighed reason is strictly discouraged. Rather than deleting information, prioritize unifying and merging the incoming inbox content smoothly into the target vault note without losing any factual density.

## Optimization: Bulk Execution
Use `execute_code` for all mechanical tasks:
- **Phase 1**: Execute `scripts/recon.py` to iterate inbox and search vault.
- **Phase 2**: (Bulk Writes) When Phase 2 generates a large number of operations (>5), use `execute_code` to perform mutations programmatically via `scripts/templates.py`.
- **Phase 4**: Static linting of output files.

## Inputs

- `<INBOX>`: folder with source .md files
- `<TARGET>`: destination folder inside the vault
- `<HUB_NAME>`: the Hub note that Spokes link back to (e.g. "Computer Vision")

## Required bundled skill

The Router must have access to the bundled `obsidian` skill. Confirm via:
`skills_list | grep -i obsidian`. If missing, install:
`hermes skills install official/note-taking/obsidian`.

## Scripts & References

- `scripts/recon.py` — Phase 1 engine. Run via `execute_code`: `python3 ~/.hermes/skills/note-taking/obsidian-injector/scripts/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>"`
- `scripts/bulk_writer.py` — Phase 3 bulk writer. Run via `execute_code`: `python3 ~/.hermes/skills/note-taking/obsidian-injector/scripts/bulk_writer.py --operations "<PATH_TO_OPS_JSON>"`
- `scripts/linter.py` — Phase 4 validator. Run via `execute_code`: `python3 ~/.hermes/skills/note-taking/obsidian-injector/scripts/linter.py --target "<TARGET>" --hub "<HUB_NAME>"`
- `scripts/templates.py` — markdown templates (template_spoke, patch_snippet).


## Ambient Discovery

To discover the directory structure of the `<INBOX>` or `<TARGET>` folders cleanly:
- **Do not** use `search_files` with `*` or generic patterns without a path scope, as it will return workspace root internals and `.git` repository objects.
- **Do** list files in the target directory using shell commands:
  ```bash
  find "/path/to/dir" -maxdepth 2 -not -path '*/.*' -name '*.md'
  ```
- **Do** list files programmatically inside `execute_code` using Python:
  ```python
  from pathlib import Path
  print([str(p) for p in Path("/path/to/dir").glob("**/*.md")])
  ```

## Pitfalls
- **read_file Deduplication**: When using `read_file` inside an `execute_code` loop, if a file was already read in the conversation, the tool returns a dedup message instead of content. For reliable bulk reading in scripts, use `terminal(f"cat {shell_quote(path)}")`.
- **Semantic Noise**: `recon.py` can produce false positive collisions for generic terms (e.g., 'PIL', 'TABLE', 'ZERO'). See `references/recon-noise.md` for common noise terms and filtering strategies.
- **Path Quoting**: Vault paths containing spaces or apostrophes (e.g., "Alex's Second Brain") must be handled with `shell_quote` when passed to `terminal()`.

