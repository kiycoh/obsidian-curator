import argparse
import json
import os
import re
from pathlib import Path

def extract_concepts(file_path: Path) -> set:
    concepts = set()
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return concepts

    # H1 and H2
    for match in re.finditer(r'^(?:#|##)\s+(.+)$', content, re.MULTILINE):
        concept = match.group(1).strip()
        if 2 < len(concept) < 60:  # Reasonable length constraint
            concepts.add(concept)

    # Bold text
    for match in re.finditer(r'\*\*(.+?)\*\*', content):
        concept = match.group(1).strip()
        if 2 < len(concept) < 60:
            concepts.add(concept)

    # Optional: Capitalized noun phrases could be added here, 
    # but bold and headings are usually high-signal enough for Obsidian.
    return concepts

def build_search_patterns(concepts: set) -> dict:
    patterns = {}
    for c in concepts:
        # Escape regex chars but allow word boundaries
        escaped = re.escape(c)
        # Using word boundaries and case-insensitivity
        patterns[c] = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
    return patterns

def run_recon(inbox_dir: Path, vault_dir: Path) -> list:
    # 1. Extract concepts from Inbox
    inbox_data = {} # filepath -> set of concepts
    all_concepts = set()
    
    for md_file in inbox_dir.glob('**/*.md'):
        concepts = extract_concepts(md_file)
        inbox_data[str(md_file)] = concepts
        all_concepts.update(concepts)

    if not all_concepts:
        return []

    # 2. Prepare search
    patterns = build_search_patterns(all_concepts)
    
    # hit_counts: concept -> { path -> count }
    hit_counts = {c: {} for c in all_concepts}

    # 3. Scan Vault
    # Exclude typical hidden or system folders like .obsidian, .git
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.md'):
                vault_file = Path(root) / file
                try:
                    content = vault_file.read_text(encoding='utf-8')
                except Exception:
                    continue
                
                # Check all patterns
                for concept, pattern in patterns.items():
                    matches = len(pattern.findall(content))
                    if matches > 0:
                        hit_counts[concept][str(vault_file)] = matches

    # 4. Format Output
    output = []
    for filepath, concepts in inbox_data.items():
        file_record = {
            "file": filepath,
            "collisions": [],
            "new_concepts": []
        }
        for c in concepts:
            c_hits = hit_counts[c]
            total_hits = sum(c_hits.values())
            if total_hits > 0:
                file_record["collisions"].append({
                    "name": c,
                    "hit_count": total_hits,
                    "hits": [{"path": k, "count": v} for k, v in sorted(c_hits.items(), key=lambda x: x[1], reverse=True)[:3]] # Top 3 hits
                })
            else:
                file_record["new_concepts"].append(c)
        
        # Sort collisions by highest hit count first
        file_record["collisions"].sort(key=lambda x: x["hit_count"], reverse=True)
        # Sort new concepts alphabetically
        file_record["new_concepts"].sort()
        output.append(file_record)

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mechanical Recon for Hermes Pipeline")
    parser.add_argument("--inbox", required=True, type=str, help="Path to the inbox directory")
    parser.add_argument("--vault", required=True, type=str, help="Path to the vault directory")
    
    args = parser.parse_args()
    
    inbox_path = Path(args.inbox)
    vault_path = Path(args.vault)
    
    if not inbox_path.exists() or not vault_path.exists():
        print(json.dumps({"error": "Inbox or Vault path does not exist."}))
        exit(1)
        
    result = run_recon(inbox_path, vault_path)
    print(json.dumps(result, indent=2))
