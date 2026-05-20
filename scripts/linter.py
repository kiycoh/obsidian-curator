import os, re, sys, yaml, argparse

# Dynamic Hermes Tools Integration
try:
    import hermes_tools
    HAS_HERMES = True
except ImportError:
    HAS_HERMES = False


def validate_note(path, hub):
    errors = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Valid Frontmatter
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not fm_match:
            errors.append("Missing or invalid frontmatter")
        else:
            try:
                yaml.safe_load(fm_match.group(1))
            except Exception as e:
                errors.append(f"YAML error: {e}")
        
        # 2. Outgoing wikilink to Hub
        if f"[[{hub}]]" not in content:
            errors.append(f"Missing wikilink to [[{hub}]]")
            
        # 3. Atomicity (approx 40 lines / 1500 chars)
        lines = content.splitlines()
        if len(lines) > 60:
            errors.append(f"Note too long ({len(lines)} lines)")
        if len(content) > 3000:
            errors.append(f"Note too large ({len(content)} chars)")
            
    except Exception as e:
        errors.append(f"Read error: {e}")
        
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Target folder in the vault")
    parser.add_argument("--hub", required=True, help="Hub note name for wikilink validation")
    args = parser.parse_args()

    if not os.path.isdir(args.target):
        print(f"Error: Target directory {args.target} does not exist.")
        sys.exit(1)

    results = {}
    for f in os.listdir(args.target):
        if f.endswith('.md'):
            path = os.path.join(args.target, f)
            errs = validate_note(path, args.hub)
            if errs:
                results[f] = errs
    
    if not results:
        print("All files validated successfully.")
    else:
        print(f"Validation failed for {len(results)} files:")
        for f, errs in results.items():
            print(f"- {f}: {', '.join(errs)}")
        sys.exit(1)
