import argparse
import json
import os
import sys

# Add script directory to path to import templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import templates

# Dynamic Hermes Tools Integration
try:
    import hermes_tools
    HAS_HERMES = True
except ImportError:
    HAS_HERMES = False

def write_note(path, content):
    if HAS_HERMES:
        try:
            hermes_tools.write_file(path=path, content=content)
            return True
        except Exception as e:
            # Fall back to local file system if RPC fails
            print(f"Hermes RPC write_file failed for {path}: {e}. Falling back to OS write.", file=sys.stderr)
    
    # Standalone fallback / local filesystem
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Failed to write note to {path}: {e}", file=sys.stderr)
        return False

def read_note(path):
    if HAS_HERMES:
        try:
            res = hermes_tools.read_file(path=path)
            if isinstance(res, dict) and "content" in res:
                return res["content"]
        except Exception as e:
            print(f"Hermes RPC read_file failed for {path}: {e}. Falling back to OS read.", file=sys.stderr)
            
    # Standalone / fallback
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Failed to read note from {path}: {e}", file=sys.stderr)
    return None

def main():
    parser = argparse.ArgumentParser(description="Bulk note writer and patcher for Hermes obsidian-curator")
    parser.add_argument("--operations", required=True, help="Path to JSON file containing operations")
    args = parser.parse_args()

    if not os.path.exists(args.operations):
        print(json.dumps({"error": f"Operations file {args.operations} does not exist"}))
        sys.exit(1)

    try:
        with open(args.operations, 'r', encoding='utf-8') as f:
            ops = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse operations JSON: {e}"}))
        sys.exit(1)

    results = []
    success_count = 0

    for idx, op in enumerate(ops):
        op_type = op.get("op")
        path = op.get("path")
        
        if not path:
            results.append({"index": idx, "success": False, "error": "Missing 'path' parameter"})
            continue

        if op_type == "write":
            heading = op.get("heading")
            snippet = op.get("snippet", "")
            hub = op.get("hub")
            tags = op.get("tags")
            related = op.get("related")

            if not heading or not hub:
                results.append({"index": idx, "path": path, "success": False, "error": "Missing 'heading' or 'hub' parameter for write operation"})
                continue

            content = templates.template_spoke(
                heading=heading,
                snippet=snippet,
                hub=hub,
                tags=tags,
                related=related
            )
            
            ok = write_note(path, content)
            if ok:
                success_count += 1
            results.append({"index": idx, "path": path, "op": "write", "success": ok})

        elif op_type == "patch":
            heading = op.get("heading")
            snippet = op.get("snippet")
            source_basename = op.get("source_basename")

            if not heading or not snippet or not source_basename:
                results.append({"index": idx, "path": path, "success": False, "error": "Missing 'heading', 'snippet', or 'source_basename' for patch operation"})
                continue

            existing_content = read_note(path)
            if existing_content is None:
                results.append({"index": idx, "path": path, "success": False, "error": "Cannot patch; target file does not exist"})
                continue
            
            patch_text = templates.patch_snippet(
                heading=heading,
                snippet=snippet,
                source_basename=source_basename
            )
            
            new_content = existing_content.rstrip() + "\n" + patch_text
            
            ok = write_note(path, new_content)
            if ok:
                success_count += 1
            results.append({"index": idx, "path": path, "op": "patch", "success": ok})

        else:
            results.append({"index": idx, "path": path, "success": False, "error": f"Unknown operation type: {op_type}"})

    report = {
        "success": success_count == len(ops),
        "total_operations": len(ops),
        "successful_operations": success_count,
        "results": results
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
