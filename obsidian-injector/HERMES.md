# Hermes — Obsidian Note-Taking Playbook (Injector, Curator, Merger)

You orchestrate the note-taking pipeline for the **Injector** (ingestion), the **Curator** (restructuring/decoupling), and the **Merger** (duplicate note unification) pipelines.

## Script & Configuration Paths
Depending on the environment, the python script and skill root folder paths are:
- **Vault Deployment**:
  - Injector & Curator `<SCRIPTS_DIR>`: `<VAULT_ROOT>/.hermes/skills/note-taking/obsidian-injector/scripts/`
  - Injector & Curator `<SKILL_ROOT>`: `<VAULT_ROOT>/.hermes/skills/note-taking/obsidian-injector/`
  - Merger `<MERGER_SCRIPTS_DIR>`: `<VAULT_ROOT>/.hermes/skills/note-taking/obsidian-merger/scripts/`
- **Skill Repository**:
  - Injector & Curator `<SCRIPTS_DIR>`: `~/.hermes/skills/note-taking/obsidian-injector/scripts/`
  - Injector & Curator `<SKILL_ROOT>`: `~/.hermes/skills/note-taking/obsidian-injector/`
  - Merger `<MERGER_SCRIPTS_DIR>`: `~/.hermes/skills/note-taking/obsidian-merger/scripts/`

- **Prompts directory** (both deployments): `<SKILL_ROOT>/prompts/`
  Used by Router actions that need to read `distiller_prompt.txt`.

Locate the active skill folder and prompts directory first (e.g. check if the vault contains `.hermes/` or use the user home fallback) before running scripts or reading template files.

## Skill & Workflow Selection

You can dynamically choose which workflow to activate based on the target files and scope of the task. However, **if the user explicitly requests or triggers a specific skill** (for example, using prefix commands like `/obsidian-injector`, `/obsidian-curator`, or `/obsidian-merger`), you **must** prioritize and adhere to that requested workflow.

## Tool Allocation

| Action                               | Who      | How                                  |
|--------------------------------------|----------|--------------------------------------|
| Extract concepts & check collisions   | Router   | execute_code (Python scripts)        |
| Compare inbox-vs-vault concepts      | Distiller subagent | delegate_task with custom prompt + payload pointers on disk (2 read_file calls: one for prompt, one for payload) |
| Decide enrich/create/skip/reformat   | Router   | internal reasoning                   |
| Generate markdown body per write     | Router   | internal reasoning                   |
| Execute write_file / patch / move    | Router   | direct file-tool primitives          |
| Validate written files               | Router   | execute_code (Python static linter)  |

**Never** use subagents for routine extraction or writing files. Use `execute_code` for mechanical multi-step work (reading files, searching, linting). Delegate the inbox-vs-vault concept comparison to Distiller subagents via pre-distilled payload and custom prompt files on disk (one read_file call on the generated prompt file, and one read_file call on the payload file). Partition large payloads into batches at the `distiller_payload.py` `--limit`/`--offset` stage rather than at the inbox stage.

---

## Workflows

### 1. Obsidian Injector Workflow
Used to ingest external source notes from an `<INBOX>` folder into a designated `<TARGET>` folder under `<HUB_NAME>`.

- **Phase 1 — Mechanical Recon & Micro-Batching**:
  * By default, the Router **must** run reconnaissance over the entire `<INBOX>` using `recon.py`:
    
    ```bash
    python3 <SCRIPTS_DIR>/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>" \
        > /tmp/recon.json
    ```

  * **Large Inbox / Truncation Fallback**: Only if the recon output is truncated (e.g. context limit exceeded or tool output cutoff) or too large to process, the Router **must** partition and process the inbox in sequential batches of **10 to 20 files** using the `--limit` and `--offset` flags on `recon.py` directly:
    ```bash
    python3 <SCRIPTS_DIR>/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>" --limit 15 --offset 0 > /tmp/recon.json
    ```
    *(Note: `recon.py` automatically sorts files alphabetically, supports pagination via --offset, and ignores any files already located in a `<INBOX>/done/` subfolder).*
- **Phase 2.0 — Router Pre-distillation (Mechanical, no LLM)**:
  * The Router runs `distiller_payload.py` via `execute_code` to extract excerpts from the inbox files and the colliding vault notes, packaging them into a single payload file.
  * If the total concept count is high, the Router partitions the payload into smaller batches of ≤10 concepts each to prevent subagent context bloat:
    ```bash
    # Single-payload mode
    python3 <SCRIPTS_DIR>/distiller_payload.py \
        --recon-report /tmp/recon.json \
        --out /tmp/distiller_payload.json

    # Partitioned mode (creates /tmp/distiller_payload_0.json, _1.json, etc.)
    python3 <SCRIPTS_DIR>/distiller_payload.py \
        --recon-report /tmp/recon.json \
        --max-concepts 10 \
        --out /tmp/distiller_payload.json
    ```
  * The Router reads the output or the generated batch files. If only `/tmp/distiller_payload.json` exists, it proceeds to **Phase 2.1a**. If multiple numbered partition files exist, it proceeds to **Phase 2.1b**.

- **Phase 2.1a — Single-batch delegation (Router → prep_delegation.py then delegate_task)**:
  * The Router runs `prep_delegation.py` via `execute_code` to prepare the exact task context:
    ```bash
    python3 <SCRIPTS_DIR>/prep_delegation.py \
        --protocol <SKILL_ROOT>/prompts/distiller_prompt.txt \
        --payload /tmp/distiller_payload.json \
        --substitute TARGET="<TARGET>" \
        --out /tmp/delegation_args.json
    ```
  * The Router reads `/tmp/delegation_args.json` verbatim and passes the parsed tasks array directly to `delegate_task`:
    ```python
    tasks_data = json.loads(read_file("/tmp/delegation_args.json"))
    delegate_task(tasks=tasks_data)
    ```
  * Once the subagent returns, the Router sanitizes the raw output file:
    ```bash
    python3 <SCRIPTS_DIR>/parse_distiller_output.py \
        --in /tmp/distiller_output_0.txt \
        --out /tmp/distiller_output_0.json
    ```
  * The Router then runs the operations validator:
    ```bash
    python3 <SCRIPTS_DIR>/validate_operations.py \
        --operations /tmp/distiller_output_0.json \
        --payload /tmp/distiller_payload.json \
        --target "<TARGET>" \
        --out /tmp/operations.validated.json
    ```

- **Phase 2.1b — Parallel batch fan-out (Router → prep_delegation.py with multiple payloads then delegate_task)**:
  * The Router compiles all generated partition files into a single delegation argument JSON using `prep_delegation.py`:
    ```bash
    # Example for 3 batches
    python3 <SCRIPTS_DIR>/prep_delegation.py \
        --protocol <SKILL_ROOT>/prompts/distiller_prompt.txt \
        --payload /tmp/distiller_payload_0.json \
        --payload /tmp/distiller_payload_1.json \
        --payload /tmp/distiller_payload_2.json \
        --substitute TARGET="<TARGET>" \
        --out /tmp/delegation_args.json
    ```
  * The Router reads `/tmp/delegation_args.json` verbatim and passes the parsed tasks array directly to `delegate_task`:
    ```python
    tasks_data = json.loads(read_file("/tmp/delegation_args.json"))
    delegate_task(tasks=tasks_data)
    ```
  * The Sub-Agents fan out via ThreadPoolExecutor. The Router sanitizes each batch's raw output file (e.g. `parse_distiller_output.py --in /tmp/distiller_output_i.txt --out /tmp/distiller_output_i.json`).
  * The Router merges all clean `"updates"` arrays into a single `/tmp/operations.json` file.
  * The Router then runs the validation script across the merged list of operations:
    ```bash
    python3 <SCRIPTS_DIR>/validate_operations.py \
        --operations /tmp/operations.json \
        --payload /tmp/distiller_payload_0.json \
        --payload /tmp/distiller_payload_1.json \
        --payload /tmp/distiller_payload_2.json \
        --target "<TARGET>" \
        --out /tmp/operations.validated.json
    ```

- **Phase 2.2 — Handle Rejection & Validation Check**:
  * **Validator exit code 2 ($\ge 10\%$ rejection):** The Router does NOT proceed to Phase 3. It must either:
    - **(a)** Inspect `operations.rejected.json`; if rejections cluster on a single batch (e.g. one distiller subagent went off the rails), re-run that single batch with `prep_delegation.py` + a stronger model.
    - **(b)** Otherwise abort the run, log the rejection summary, and surface to the user. Do NOT attempt auto-routing of "rejected patch $\rightarrow$ write" — that bypasses the validator's intent.
  * **Validator exit code 0 ($< 10\%$ rejection):** Proceed to Phase 3 with the successfully validated operations list `/tmp/operations.validated.json`.

- **Phase 3 — Execute**:
  Mutate the files in the vault. We always write programmatically via the bulk writer to ensure consistent templating and validation:
  ```bash
  python3 <SCRIPTS_DIR>/bulk_writer.py --operations "/tmp/operations.validated.json"
  ```

- **Phase 4 — Validate & Cleanup**:
  Run `linter.py` to check YAML syntax, wikilinks, and 40-line atomicity for ONLY the modified/created notes:
  ```bash
  python3 <SCRIPTS_DIR>/linter.py --operations "/tmp/operations.validated.json" --hub "<HUB_NAME>"
  ```
  *(Note: You can still run with `--target "<TARGET>"` to validate the entire folder if needed).*

  If and ONLY if the validation succeeds, move the successfully processed inbox files to the `done/` subfolder:
  ```bash
  mkdir -p "<INBOX>/done"
  mv <path_to_processed_inbox_files> "<INBOX>/done/"
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
- `recon.py` JSON > 200 concepts → mandatory partition via `distiller_payload.py` `--max-concepts`; never single-shot delegate.
- Single payload > 80KB or containing too many concepts → mandatory partition via `--max-concepts` to avoid bloating subagent context.
- Parallel batch > `max_concurrent_children` (default 30) → tool errors out rather than truncating; either shrink the batch or raise the config.
- Validator exits with code 2 ($\ge 10\%$ operations rejected) $\rightarrow$ abort batch immediately. Re-recon or upgrade the subagent model.
- Distiller returns updates with `heading` values NOT present in the payload → abort batch and re-recon; indicates context-field truncation or model hallucination.
- Subagent timeout (`child_timeout_seconds`, default 600s) → check `~/.hermes/logs/subagent-timeout-<session>-<timestamp>.log` for the diagnostic; usually OpenRouter rate-limit or tool-schema rejection.
- Router context > 60k tokens at any point → stop, report incomplete plan.

## Pitfalls & Shell Quoting
- **Nested Quoting in f-strings**: When constructing python/bash execution strings, using `shell_quote(TARGET)` or similar helpers generates an already-quoted string. Do **NOT** wrap the `{shell_quote(...)}` block in extra single or double quotes (e.g. `TARGET='{shell_quote(folder)}'`), as this results in nested matching errors in the shell (e.g. `eval: unexpected EOF while looking for matching ...`). Use it as: `--substitute TARGET={shell_quote(folder)}`.
- **recon.py stderr behaviour**: In JSON mode, `recon.py` suppresses stats on stderr to prevent output stream pollution when captured. Do NOT redirect stderr to a file (like `2>/tmp/recon.stderr`) in JSON mode as it creates a confusing empty file.
- **hermes_tools.read_file line format**: `hermes_tools.read_file` returns file content prefixed with line numbers (`LINE|CONTENT`). To load subagent JSON files via Python or command-line, strip line numbers before `json.loads` or use shell commands like `terminal(f"cat {shell_quote(path)}")` instead.