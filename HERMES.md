# Hermes — Obsidian Curator Router

You orchestrate the obsidian-curator workflow. The reading, extraction, and collision checking of source files is performed mechanically via Python scripts (execute_code). Semantic decisions, formatting, and file mutations (writing/patching) are performed directly by you (the Router).

## Tool Allocation

| Action                               | Who      | How                                  |
|--------------------------------------|----------|--------------------------------------|
| Extract concepts & search vault      | Router   | execute_code (Python script)         |
| Decide enrich/create/skip            | Router   | internal reasoning                   |
| Generate markdown body per write     | Router   | internal reasoning                   |
| Execute write_file / patch           | Router   | direct file-tool primitives          |
| Validate written files               | Router   | execute_code (Python static linter)  |

**Never** use subagents for routine extraction or writing files. Use `execute_code` for mechanical multi-step work (reading files, searching, linting). Delegate reasoning-heavy tasks to a subagent ONLY if the input data (e.g., a massive inbox) exceeds your context budget.

## Flow — 4 Phases, Sequential

### Phase 1 — Mechanical Recon (Router, execute_code)

Do not write your own Python script. Execute the pre-written mechanical recon script using `execute_code`:
```bash
python ~/.hermes/skills/note-taking/obsidian-curator/scripts/recon.py --inbox "<INBOX>" --vault "<VAULT_ROOT>"
```
This script will mechanically extract candidate concepts (H1/H2, bold text) and check for vault collisions. It outputs an ultra-compact JSON structure grouping items by collision presence: `[{"file": "...", "collisions": [{"name": "...", "hit_count": N, "hits": [{"path": "...", "count": N}]}], "new_concepts": ["Concept 1", "Concept 2"]}]`.

Do not use LLM calls or subagents for this step. Rely entirely on the output of `recon.py`.

### Phase 2 — Semantic Orchestration (Router, internal)

**CRITICAL INSTRUCTION**: You must completely process **EVERY SINGLE FILE** present in the Phase 1 JSON. Do not stop until all source files have been mapped and all information has been integrated into the vault.

Review the JSON mapping from Phase 1. For each file, read its actual source content (via `read_file` or bulk Python scripts), and then make the semantic decision `create`, `enrich`, or `skip` in-context based on the `collisions` and `new_concepts` lists:
- Concept is in `new_concepts` → operation = `create` (path = `<TARGET>/<slug>.md`, AI = true, body = template_spoke)
- Concept is in `collisions` & `hit_count > threshold` & new content signal → operation = `enrich` (path = mapped `path`, AI = false, body = patch_snippet)
- Otherwise → operation = `skip`

Only if the inbox is excessively large (>50 files, >200 concepts) should you consider delegating this reasoning-heavy Phase as a single task to a subagent using the JSON from Phase 1 as context.

Build a finalized list of write operations for ALL files. Each entry has: `op` (write_file|patch),
`path`, `content` (the literal markdown to write or append).

### Phase 3 — Execute Writes (Router, internal)

For each operation in the plan, execute `write_file` or `patch` directly using your
native file editing tools. Do NOT use subagents for this step.
Verify each operation succeeds.

### Phase 4 — Validate (Router, execute_code)

Perform a final pass using a static linter script via `execute_code`. The Python script must inspect the written files in `<TARGET>` and verify:
1. Valid frontmatter (YAML parse).
2. Presence of necessary outgoing wikilinks (`[[<HUB_NAME>]]`) via regex.
3. Atomicity (approx. 40 lines / 1500 chars per note) using `len()` or `wc -l`.

Print a final report. If any failures occur, list them — do NOT auto-retry.

## Absorbed Principles

1. **Elegant Injection** — Router-generated markdown matches vault schema
   (frontmatter, Italian body, wikilinks).
2. **Anti-Fragmentation** — Phase 1 content-search catches non-canonically
   named existing notes; no duplicate Spokes for renamed files.
3. **Hub-and-Spoke** — every create includes `[[<HUB_NAME>]]` in body.
4. **OFM Compliance** — validated by the linter at Phase 4.
5. **AI Provenance** — set in Phase 2 markdown generation, frozen at write.
6. **Atomicity** — 40 lines / 1500 chars per Spoke; enforced at Phase 4.

## Hard Stops

- Phase 1 JSON becomes too large (>200 concepts) → delegate Phase 2 decision or abort and ask user.
- Router context > 60k tokens at any point → stop, report incomplete plan.
