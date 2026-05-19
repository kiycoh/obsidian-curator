---
name: obsidian-curator
description: "Inject Pipeline — ingests source markdown from an inbox into the Obsidian vault. Performs mechanical recon via execute_code, reasoning in-context, and file writes directly from the Router."
---

# Obsidian Curator — Inject Pipeline

Workflow defined in HERMES.md. This skill is the entrypoint; HERMES.md is the playbook.

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

- `scripts/recon.py` — Phase 1 engine. Run via `execute_code`: `python ~/.hermes/skills/note-taking/obsidian-curator/scripts/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>"`
- `scripts/linter.py` — Phase 4 validator. Run via `execute_code`: `python ~/.hermes/skills/note-taking/obsidian-curator/scripts/linter.py --target "<TARGET>" --hub "<HUB_NAME>"`
- `scripts/templates.py` — markdown templates (template_spoke, patch_snippet).

## Pitfalls
- **read_file Deduplication**: When using `read_file` inside an `execute_code` loop, if a file was already read in the conversation, the tool returns a dedup message instead of content. For reliable bulk reading in scripts, use `terminal(f"cat {shell_quote(path)}")`.
- **Path Quoting**: Vault paths containing spaces or apostrophes (e.g., "Alex's Second Brain") must be handled with `shell_quote` when passed to `terminal()`.
