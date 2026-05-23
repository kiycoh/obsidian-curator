import re

LIMITS = {"max_lines": 60, "max_chars": 6000, "lean_chars": 600}

def metrics(content):
    return {"char_count": len(content), "line_count": len(content.splitlines())}

def is_lean(content):
    return len(content.strip()) < LIMITS["lean_chars"]

def wikilink(name):
    return f"[[{name}]]"

def has_wikilink(content, name):
    return f"[[{name}]]" in content

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*$', re.MULTILINE)

def parse_headings(body):
    return [{"level": len(m.group(1)), "text": m.group(2), "pos": m.start()}
            for m in HEADING_RE.finditer(body)]

def sections_by_h2(body):
    """Split body at H2 boundaries. Each section's content includes nested H3+.
    Returns [{'title': str, 'content': str}]."""
    heads = [h for h in parse_headings(body) if h["level"] == 2]
    out = []
    for i, h in enumerate(heads):
        start = h["pos"]
        end = heads[i + 1]["pos"] if i + 1 < len(heads) else len(body)
        block = body[start:end]
        section_body = block.split("\n", 1)[1] if "\n" in block else ""
        out.append({"title": h["text"], "content": section_body.strip()})
    return out
