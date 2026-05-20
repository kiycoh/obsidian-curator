import datetime, re

def slugify(s: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s.strip().replace('  ', ' ')  # keep spaces, Obsidian likes them

def clean_tag(t: str) -> str:
    t = re.sub(r'^[\d\.]+\s*', '', t)
    t = t.lower()
    t = re.sub(r'[^a-z0-9\s-]', '', t)
    t = re.sub(r'[\s_]+', '-', t)
    return t.strip('-')

def template_spoke(heading: str, snippet: str, hub: str, tags: list[str] = None, related: list[str] = None) -> str:
    today = datetime.date.today().strftime("%Y, %m, %d")
    body = snippet.strip() or "(da espandere)"
    
    # parent note link
    parent_note = f'"[[{hub}]]"'
    
    # related list
    related_items = [f'"[[{hub}]]"']
    if related:
        for r in related:
            r_link = f'"[[{r}]]"'
            if r_link not in related_items:
                related_items.append(r_link)
    
    # tags list
    tag_list = []
    if tags:
        for t in tags:
            ct = clean_tag(t)
            if ct and ct not in tag_list:
                tag_list.append(ct)
    else:
        # default tag derived from hub
        ch = clean_tag(hub)
        if ch:
            tag_list.append(ch)
            
    # Format YAML components
    related_yaml = "\n".join(f"  - {item}" for item in related_items)
    tags_yaml = "\n".join(f"  - {tag}" for tag in tag_list)
    
    frontmatter = f"""---
parent note: {parent_note}
related:
{related_yaml}
tags:
{tags_yaml}
last modified: {today}
AI: true
---"""

    return f"""{frontmatter}

# {heading}

{body}
"""

def patch_snippet(heading: str, snippet: str, source_basename: str) -> str:
    return f"""

## Note aggiuntive — {heading} (da {source_basename})

{snippet.strip()}
"""
