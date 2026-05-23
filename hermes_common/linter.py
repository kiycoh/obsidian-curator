# --- hermes_common bootstrap (uniform across all hermes skills) ---
import os, sys
_p = os.path.dirname(os.path.abspath(__file__))
while _p != os.path.dirname(_p) and not os.path.isdir(os.path.join(_p, "hermes_common")):
    _p = os.path.dirname(_p)
if _p not in sys.path:
    sys.path.insert(0, _p)
# --- end bootstrap ---

import os, re, sys, yaml, json, argparse
from hermes_common import ofm, frontmatter

# Dynamic Hermes Tools Integration
try:
    import hermes_tools
    HAS_HERMES = True
except ImportError:
    HAS_HERMES = False


def resolve_hub_name(note_path, hub_arg):
    """
    Resolve the actual hub note name. If a markdown file matching hub_arg (or starting with it)
    exists in the same directory as note_path, return its basename (without .md).
    Otherwise, return hub_arg itself.
    """
    dir_path = os.path.dirname(note_path)
    if not os.path.isdir(dir_path):
        return hub_arg

    # Check exact match first
    exact_file = os.path.join(dir_path, f"{hub_arg}.md")
    if os.path.isfile(exact_file):
        return hub_arg

    # Look for a file starting with hub_arg (case-insensitive) in the same folder
    try:
        hub_lower = hub_arg.lower()
        candidates = []
        for f in os.listdir(dir_path):
            if f.lower().startswith(hub_lower) and f.endswith(".md"):
                candidates.append(f[:-3])
        if candidates:
            candidates.sort(key=len)
            return candidates[0]
    except Exception:
        pass

    return hub_arg


def validate_note(path, hub, op_type=None):
    errors = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        data, _, _ = frontmatter.split(content)
        if data is None:
            errors.append("Missing or invalid frontmatter")

        # Resolve the actual hub name from the file's parent directory
        resolved_hub = resolve_hub_name(path, hub)

        # hub wikilink: required for spoke write/patch; NOT for hub-index/reformat/merge overwrites
        if op_type != "overwrite" and not ofm.has_wikilink(content, resolved_hub):
            errors.append(f"Missing wikilink to [[{resolved_hub}]]")

        # atomicity: skip for patch (append) only
        if op_type != "patch":
            m = ofm.metrics(content)
            if m["line_count"] > ofm.LIMITS["max_lines"]:
                errors.append(f"Note too long ({m['line_count']} lines)")
            if m["char_count"] > ofm.LIMITS["max_chars"]:
                errors.append(f"Note too large ({m['char_count']} chars)")
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

    files_to_check = [] # List of tuples: (path, op_type)
    if args.files:
        for f in args.files:
            files_to_check.append((f, None))
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
                if op.get("op") == "delete":
                    continue
                path = op.get("path")
                if path and path.endswith('.md'):
                    files_to_check.append((path, op.get("op")))
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
                files_to_check.append((os.path.join(args.target, f), None))


    results = {}
    for path, op_type in files_to_check:
        if os.path.exists(path):
            errs = validate_note(path, args.hub, op_type)
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
            for fname, errs in results.items():
                print(f"  - {fname}:")
                for err in errs:
                    print(f"    * {err}")
            sys.exit(1)
