---
name: obsidian-merger
description: "Merge & Unification Pipeline — identifies duplicate notes of the same name located in different folders across the vault, and merges their contents smoothly into a single canonical note without losing technical density."
---

# Obsidian Merger — Merge Pipeline

The Merge pipeline is used to find and resolve duplicate note files within the vault. In Obsidian, while you cannot have files with the exact same name in the same directory, you can have duplicates in different folders (e.g. `1.1 Informazione/MLP.md` and `1.2 Calcolo/MLP.md`).

## Inputs

- `<VAULT_ROOT>`: path to the root of the Obsidian vault.
- `<FOLDER_PATH>` (Optional): specific subdirectory to restrict the duplicate scan.

## Required Tools

This skill requires:
- **`find_duplicates.py`** (executed via `execute_code`) to locate identical note basenames across the vault, optionally scoped using the `--folder` parameter.
- **`web_search` & `web_extract`** (native tools or programmatically imported via `hermes_tools`) to verify facts, definitions, or correct formulas.
- **`write_file` & `patch`** (native file operation tools) to commit updates to the vault.

## Merge Workflow

- **Phase 1 — Locate Duplicates**:
  Run the duplicate locator script using `execute_code`:
  ```bash
  python3 ~/.hermes/skills/note-taking/obsidian-merger/scripts/find_duplicates.py --vault "<VAULT_ROOT>" [--folder "<SUBDIRECTORY_PATH>"]
  ```
- **Phase 2 — Semantic Unification**:
  Read each duplicate note's content. Select a single canonical target path (usually the most relevant subdirectory). Integrate all facts, definitions, and formatting from the duplicates into a single, cohesive canonical note body without losing technical details or references.
- **Phase 3 — Execution & Cleanup**:
  Write the merged body to the canonical file path. Delete all obsolete duplicate files from the vault.
- **Phase 4 — Validate**:
  Run `linter.py` to ensure the merged note meets atomicity (max 6000 chars), YAML frontmatter, and link rules.

## Content Preservation & Deletion Rules

- **Strict Anti-Deletion Policy**: Deleting existing information during merge consolidation is **strictly discouraged** unless:
  1. The information is pure semantic/formatting noise.
  2. The model is rewriting/expanding that same concept in a more thorough, detailed, and academically rigorous manner.
  3. The model has verified via `web_search` that the original phrase, definition, or formula is factually incorrect.
- **Enrichment Trigger**: If the unified note contains **fewer than 600 characters**, it must be enriched with external web sources.
