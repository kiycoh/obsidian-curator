import os, re, sys, yaml, json, argparse

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
        if len(content) > 6000:
            errors.append(f"Note too large ({len(content)} chars)")
            
    except Exception as e:
        errors.append(f"Read error: {e}")
        
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Target folder in the vault")
    parser.add_argument("--operations", help="Path to JSON file containing operations")
    parser.add_argument("--files", nargs="+", help="Specific file paths to validate")
    parser.add_argument("--hub", required=True, help="Hub note name for wikilink validation")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (text or json)")
    args = parser.parse_args()

    if not args.target and not args.operations and not args.files:
        if args.format == "json":
            print(json.dumps({"error": "Either --target, --operations, or --files must be specified."}))
        else:
            print("Error: Either --target, --operations, or --files must be specified.")
        sys.exit(1)

    files_to_check = []
    if args.files:
        files_to_check.extend(args.files)
    elif args.operations:
        if not os.path.exists(args.operations):
            if args.format == "json":
                print(json.dumps({"error": f"Operations file {args.operations} does not exist."}))
            else:
                print(f"Error: Operations file {args.operations} does not exist.")
            sys.exit(1)
        try:
            with open(args.operations, 'r', encoding='utf-8') as f:
                ops = json.load(f)
            for op in ops:
                path = op.get("path")
                # Only check files that were written or patched
                if path and op.get("op") in ("write", "patch") and path.endswith('.md'):
                    files_to_check.append(path)
        except Exception as e:
            if args.format == "json":
                print(json.dumps({"error": f"Failed to parse operations JSON: {e}"}))
            else:
                print(f"Error: Failed to parse operations JSON: {e}")
            sys.exit(1)
    elif args.target:
        if not os.path.isdir(args.target):
            if args.format == "json":
                print(json.dumps({"error": f"Target directory {args.target} does not exist."}))
            else:
                print(f"Error: Target directory {args.target} does not exist.")
            sys.exit(1)
        for f in os.listdir(args.target):
            if f.endswith('.md'):
                files_to_check.append(os.path.join(args.target, f))


    results = {}
    for path in files_to_check:
        if os.path.exists(path):
            errs = validate_note(path, args.hub)
            if errs:
                results[os.path.basename(path)] = errs
        else:
            results[os.path.basename(path)] = ["File does not exist"]
    
    if args.format == "json":
        print(json.dumps({
            "success": not results,
            "failed_count": len(results),
            "errors": results
        }, indent=2, ensure_ascii=False))
        if results:
            sys.exit(1)
    else:
        if not results:
            print("All files validated successfully.")
        else:
            print(f"Validation failed for {len(results)} files:")
            for f, errs in results.items():
                print(f"- {f}: {', '.join(errs)}")
            sys.exit(1)

