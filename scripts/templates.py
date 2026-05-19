import datetime, re

def slugify(s: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s.strip().replace('  ', ' ')  # keep spaces, Obsidian likes them

def template_spoke(heading: str, snippet: str, hub: str) -> str:
    today = datetime.date.today().isoformat()
    body = snippet.strip() or "(da espandere)"
    return f"""---
title: {heading}
AI: true
created: {today}
type: spoke
hub: "{hub}"
---

# {heading}

{body}

---
[[{hub}]]
"""

def patch_snippet(heading: str, snippet: str, source_basename: str) -> str:
    return f"""

## Note aggiuntive — {heading} (da {source_basename})

{snippet.strip()}
"""
