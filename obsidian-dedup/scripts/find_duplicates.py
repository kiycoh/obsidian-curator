import os, json, argparse, sys, re

def find_duplicates(vault_path, folder_path=None):
    search_path = folder_path if folder_path else vault_path
    
    # Map from normalized name to dict: {"paths": [...], "representative_name": "..."}
    groups = {}
    
    for root, dirs, files in os.walk(search_path):
        # Skip hidden folders like .git or .obsidian
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                orig_name = os.path.splitext(file)[0]
                
                # Normalize name:
                # 1. Strip parenthetical suffixes (e.g., "Subword Tokenization (NLP)" -> "Subword Tokenization")
                norm = re.sub(r'\s*\(.*?\)\s*$', '', orig_name)
                # 2. Lowercase
                norm = norm.lower()
                # 3. Strip non-alphanumeric characters
                norm = re.sub(r'[^a-z0-9]', '', norm)
                
                full_path = os.path.abspath(os.path.join(root, file))
                
                if norm not in groups:
                    groups[norm] = {
                        "paths": [],
                        "representative_name": orig_name
                    }
                groups[norm]["paths"].append(full_path)
                
                # Keep the shortest name as the representative name to avoid suffixes
                if len(orig_name) < len(groups[norm]["representative_name"]):
                    groups[norm]["representative_name"] = orig_name
                    
    # Filter only duplicates and map to their representative names
    duplicates = {}
    for norm, group in groups.items():
        if len(group["paths"]) > 1:
            duplicates[group["representative_name"]] = group["paths"]
            
    return duplicates

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault root")
    parser.add_argument("--folder", required=False, help="Subdirectory inside the vault to restrict the search")
    args = parser.parse_args()
    
    if not os.path.isdir(args.vault):
        print(json.dumps({"error": f"Vault path {args.vault} is not a directory"}))
        sys.exit(1)
        
    search_folder = None
    if args.folder:
        search_folder = os.path.abspath(args.folder)
        if not os.path.isdir(search_folder):
            print(json.dumps({"error": f"Folder path {args.folder} is not a directory"}))
            sys.exit(1)
        
    dupes = find_duplicates(args.vault, search_folder)
    print(json.dumps(dupes, indent=2))
