#!/usr/bin/env python3
"""Decouple-mode planner: H1->Hub, each H2->Spoke write op (raw section as snippet),
plus one overwrite op turning the monolith into a Hub index. Emits bulk_writer ops JSON."""
# --- hermes_common bootstrap (uniform across all hermes skills) ---
import os, sys
_p = os.path.dirname(os.path.abspath(__file__))
while _p != os.path.dirname(_p) and not os.path.isdir(os.path.join(_p, "hermes_common")):
    _p = os.path.dirname(_p)
if _p not in sys.path:
    sys.path.insert(0, _p)
# --- end bootstrap ---

import argparse, datetime, json, os, sys
from hermes_common import frontmatter, ofm, templates

def build_ops(note, parent_folder, hub):
    with open(note, encoding="utf-8") as f:
        content = f.read()
    _, _, body = frontmatter.split(content)
    sections = ofm.sections_by_h2(body)
    ops, titles = [], []
    for s in sections:
        titles.append(s["title"])
        spoke_path = os.path.join(parent_folder, f"{templates.slugify(s['title'])}.md")
        ops.append({"op": "write", "path": spoke_path, "heading": s["title"],
                    "snippet": s["content"], "hub": hub})
    hub_fm = {
        "related": [],
        "tags": [frontmatter.clean_tag(hub)],
        "last modified": datetime.date.today().strftime("%Y, %m, %d"),
        "AI": True,
    }
    index_body = f"# {hub}\n\n" + "\n".join(f"- [[{t}]]" for t in titles) + "\n"
    ops.append({"op": "overwrite", "path": note, "content": frontmatter.dump(hub_fm, index_body)})
    return ops, titles

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--note", required=True)
    ap.add_argument("--parent-folder", required=True)
    ap.add_argument("--hub", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ops, titles = build_ops(a.note, a.parent_folder, a.hub)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(ops, f, ensure_ascii=False, indent=2)
    print(f"[SPLIT] {len(titles)} spokes + 1 hub index -> {a.out}", file=sys.stderr)
