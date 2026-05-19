# Content Search Tools for Obsidian Vault

## Available Tools

When querying content in the vault, use these tools instead of `obsidian-cli`:

### 1. `search_files` (Primary Tool)

Search file contents or find files by name using regex patterns.

**For content search:**
```bash
pattern="<search term>"
target="content"  # or "files" to find filenames only
path="/path/to/vault/root"  # relative paths from vault root work too
output_mode="content"    # show matching lines with file locations
                         # "files_only" = just list files
                         # "count" = match count per file
context=3                # show N lines before/after each match (optional)
limit=50                 # max results to return
```

**Example patterns:**
- Exact phrase: `"exact phrase"`
- Boolean: `"term1" OR "term2"`, `"term1 NOT term2"`
- Prefix wildcard: `deploy*`
- Multiple terms: `"packet switching"`, `"ritardo propagazione"`
- Case-insensitive regex: `(Packet|pacchetto)`

**Recommended usage for concept collision checking:**
```bash
search_files(pattern="concept keyword", target="content", output_mode="count")
```

### 2. `read_file`

Read specific files by path to review full content before writing.

```bash
path="/absolute/path/to/file.md"   # or relative from vault root
limit=500                           # lines to read (max 2000)
offset=1                            # start line number (default: 1)
```

### 3. `search_files` with Target Files Only

When you need file list for a directory:
```bash
search_files(target="files", pattern="*.md")
# or search specific folder:
search_files(path="/vault/dir/to/search", target="files")
```

## Common Search Patterns

### Finding by English Term (with Italian translation)
```bash
search_files(pattern="(packet|pacchetto)", target="content", output_mode="count")
```

### Finding Delay/Propagation Concepts  
```bash
search_files(pattern="(delay|propagazione|ritardo)", target="content", output_mode="count")
```

### Case-Insensitive Search
Use regex with case-insensitive flag or search multiple variations:
```bash
# These approaches work:
search_files(pattern="[Pp]acket", ...)  # single char OR in regex
# Or better: use word patterns
search_files(pattern="(Packet|pacchetto|commutazione)", ...)
```

## Pitfalls to Avoid

1. **DO NOT assume `obsidian-cli` exists** - it's documented in some skills but not available in all environments
2. **Avoid guessing file paths** - always use search results from the tool output
3. **Use count mode for quick collision detection** - gives you immediate hit counts per file
4. **Language variations matter** - Italian vaults may use different terminology (e.g., "ritardo" vs "delay")

## Best Practice Workflow

1. Extract unique concepts from source file
2. For each concept, search with key terms: `search_files(pattern="term", target="content", output_mode="count")`
3. Review top files to determine if collision is CREATE/ENRICH/SKIP
4. Use file paths from search results (never guess)

---
*Last updated: 2026-05-19 - Added based on session reviewing obsidian-curator distill workflow*