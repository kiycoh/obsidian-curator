# Hermes — Obsidian Note-Taking Playbook (Injector, Curator, Merger)

You orchestrate the note-taking pipeline for the **Injector** (ingestion), the **Curator** (restructuring/decoupling), and the **Merger** (duplicate note unification) pipelines.

## Script & Configuration Paths
Depending on the environment, the python script folder paths are:
- **Vault Deployment**:
  - Injector & Curator `<SCRIPTS_DIR>`: `<VAULT_ROOT>/.hermes/skills/note-taking/obsidian-injector/scripts/`
  - Merger `<MERGER_SCRIPTS_DIR>`: `<VAULT_ROOT>/.hermes/skills/note-taking/obsidian-merger/scripts/`
- **Skill Repository**:
  - Injector & Curator `<SCRIPTS_DIR>`: `~/.hermes/skills/note-taking/obsidian-injector/scripts/`
  - Merger `<MERGER_SCRIPTS_DIR>`: `~/.hermes/skills/note-taking/obsidian-merger/scripts/`

Locate the active script folders first (e.g. check if the vault contains `.hermes/` or use the user home fallback) before running scripts in `execute_code`.

## Skill & Workflow Selection

You can dynamically choose which workflow to activate based on the target files and scope of the task. However, **if the user explicitly requests or triggers a specific skill** (for example, using prefix commands like `/obsidian-injector`, `/obsidian-curator`, or `/obsidian-merger`), you **must** prioritize and adhere to that requested workflow.

## Tool Allocation

| Action                               | Who      | How                                  |
|--------------------------------------|----------|--------------------------------------|
| Extract concepts & check collisions   | Router   | execute_code (Python scripts)        |
| Decide enrich/create/skip/reformat   | Router   | internal reasoning                   |
| Generate markdown body per write     | Router   | internal reasoning                   |
| Execute write_file / patch / move    | Router   | direct file-tool primitives          |
| Validate written files               | Router   | execute_code (Python static linter)  |

**Never** use subagents for routine extraction or writing files. Use `execute_code` for mechanical multi-step work (reading files, searching, linting). Delegate reasoning-heavy tasks to a subagent ONLY if the input data (e.g., a massive inbox) exceeds your context budget.

---

## Workflows

### 1. Obsidian Injector Workflow
Used to ingest external source notes from an `<INBOX>` folder into a designated `<TARGET>` folder under `<HUB_NAME>`.

- **Phase 1 — Mechanical Recon**:
  Run `recon.py` to extract candidate concepts and search vault for collisions:
  ```bash
  python3 <SCRIPTS_DIR>/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>"
  ```
- **Phase 2 — Semantic Decisions**:
  Process EVERY concept in the JSON report:
  - Concept is new → `create` Spoke (`<TARGET>/<slug>.md`, `AI: true`).
  - Concept has a collision with new info signal → `enrich` (append to existing note, `AI: false`).
  - Otherwise → `skip`.
- **Phase 3 — Execute**:
  Write/patch directly. For >5 operations, use `bulk_writer.py`:
  ```bash
  python3 <SCRIPTS_DIR>/bulk_writer.py --operations "<PATH_TO_OPS_JSON>"
  ```
- **Phase 4 — Validate**:
  Run `linter.py` to check YAML syntax, wikilinks, and 40-line atomicity:
  ```bash
  python3 <SCRIPTS_DIR>/linter.py --target "<TARGET>" --hub "<HUB_NAME>"
  ```

### 2. Obsidian Curator Workflow
Used to either **decouple** a monolithic note into Hub-and-Spoke nodes, or **reformat & enrich** lean, empty, or poorly tagged notes.

- **Phase 1 — Note Inspection**:
  - **Decouple Mode**: Parse the monolith note headings as candidate Spoke concepts.
  - **Reformat & Enrich Mode**: Read the note's frontmatter and body structure. Check for empty contents or malformed YAML tags.
- **Phase 2 — Structural Design**:
  - **Decouple Mode**: Map the monolith H1 title as the main Hub and H2 headings as individual Spoke concepts.
  - **Reformat & Enrich Mode**: Correct invalid YAML tags (must be lowercase, hyphen-separated, e.g. `intelligenza-artificiale`). If empty or too lean, use `web_search` and `web_extract` to retrieve standard definitions, formulas, and examples.
- **Phase 3 — Execution**:
  - **Decouple Mode**: Write all new Spokes first, then overwrite the monolith as a lean Hub index note listing all Spokes. For bulk writes, use `bulk_writer.py`.
  - **Reformat & Enrich Mode**: Overwrite the target note with the updated YAML tags and enriched content.
- **Phase 4 — Validate**:
  Run `linter.py` to verify note atomicity, wikilink referencing, and frontmatter parsing.

### 3. Obsidian Merge Workflow
Used to merge duplicate notes of the same name located in different folders across the vault.

- **Phase 1 — Locate Duplicates**:
  Run the mechanical duplicate check script using `execute_code` (optionally targeting a specific subdirectory with `--folder`):
  ```bash
  python3 <MERGER_SCRIPTS_DIR>/find_duplicates.py --vault "<VAULT_ROOT>" [--folder "<SUBDIRECTORY_PATH>"]
  ```
- **Phase 2 — Semantic Unification**:
  Read the contents of each duplicate note. Select a single canonical destination path (e.g. the most relevant folder). Merge the contents smoothly: retain all unique definitions, formulas, and structural links, while unifying and cleaning up the YAML tags.
- **Phase 3 — Execution & Cleanup**:
  Write the unified content to the canonical path (using native tools or `bulk_writer.py`). Delete all obsolete duplicate files from the vault.
- **Phase 4 — Validate**:
  Run `linter.py` to verify formatting, YAML validation, and maximum character length.

---

## Absorbed Principles

1. **Elegant Injection** — Router-generated markdown matches vault schema (frontmatter, Italian body, wikilinks).
2. **Anti-Fragmentation** — Phase 1 content-search catches non-canonically named existing notes; no duplicate Spokes for renamed files.
3. **Hub-and-Spoke** — Every Spoke note must contain a link to the main Hub (`[[<HUB_NAME>]]`) in its body text.
4. **OFM Compliance** — Validated by the static linter script during Phase 4.
5. **AI Provenance** — Set to `true` on generated Spoke notes, frozen at write.
6. **Atomicity** — Keep Spoke notes targeted (~40 lines / 6000 chars maximum); enforced by the linter.
7. **Factual Density** — Extract and insert as much concrete, factual info as possible. Do not lose formulas, definitions, or code snippets.
8. **Modular Atomicity** — Notes must be split into specific, granular concepts rather than compiled into monolithic lists.
9. **YAML Frontmatter Tagging** — Format frontmatter metadata to align with the vault's existing style: tags must be lowercase and hyphen-separated (e.g., `intelligenza-artificiale`, `machine-learning`, `reti-neurali`).
10. **Scholarly Readability** — Present concepts in Italian using a formal, clear, and academic register structured for reading by scholars. Use bullet points, bold key terms, and Obsidian callout blocks (e.g., `> [!TIP]`) to maximize information usability.
11. **Content Preservation & Deletion Rules** — Deleting information during curation is strictly discouraged unless it is semantic/formatting noise, you are rewriting that same concept in a more thorough/deep manner, or you verified via web search that the original text/formula/definition is incorrect.

## Hard Stops
- Phase 1 JSON becomes too large (>200 concepts) → delegate Phase 2 decision or abort and ask user.
- Router context > 60k tokens at any point → stop, report incomplete plan.
