# Obsidian Injector - Inject Pipeline

Ingests source markdown from an inbox into the Obsidian vault via mechanical recon, reasoning in-context, and direct file writing.

## Quick Start

To use the Obsidian Injector, the Router must have access to the bundled `obsidian` skill. You can confirm this by running:

```bash
skills_list | grep -i obsidian
```

If it is missing, install it:

```bash
hermes skills install official/note-taking/obsidian
```

To run the curation process, the pipeline requires the following inputs:
- `<INBOX>`: folder with source .md files
- `<TARGET>`: destination folder inside the vault
- `<HUB_NAME>`: the Hub note that Spokes link back to (e.g. "Computer Vision")

## Features

- **Mechanical Recon**: Utilizes Python scripts (`scripts/recon.py`) to extract candidate concepts (H1/H2, bold text) and check for vault collisions efficiently.
- **Semantic Orchestration**: Employs context-aware reasoning to decide whether to create, enrich, or skip notes based on collision analysis.
- **Automated Writing**: Performs file mutations directly, formatting them according to Obsidian Flavored Markdown (OFM) rules.
- **Validation**: Includes a static linter script (`scripts/linter.py`) to verify valid frontmatter, presence of necessary wikilinks, and atomicity of the notes.
- **Anti-Fragmentation**: Intelligent content-search prevents creating duplicate Spokes for renamed files.
- **AI Provenance**: Sets AI provenance tracking during markdown generation.

## Configuration

| Parameter | Description | Required |
|----------|-------------|---------|
| `<INBOX>` | Folder containing source .md files to process | Yes |
| `<TARGET>` | Destination folder inside the Obsidian vault | Yes |
| `<HUB_NAME>` | The Hub note that the created Spokes will link back to | Yes |

## Documentation

- [Skill Configuration](./SKILL.md)
- [Pipeline Architecture](./HERMES.md)

## License

MIT
