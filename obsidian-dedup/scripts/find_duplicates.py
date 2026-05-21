import os, json, argparse, sys

def find_duplicates(vault_path, folder_path=None):
    search_path = folder_path if folder_path else vault_path
    
    # Map from lowercase filename (without extension) to list of full file paths
    name_map = {}
    
    for root, dirs, files in os.walk(search_path):
        # Skip hidden folders like .git or .obsidian
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.md'):
                name_lower = file.lower()
                basename = os.path.splitext(name_lower)[0]
                full_path = os.path.abspath(os.path.join(root, file))
                
                if basename not in name_map:
                    name_map[basename] = []
                name_map[basename].append(full_path)
                
    # Filter only duplicates
    duplicates = {name: paths for name, paths in name_map.items() if len(paths) > 1}
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
