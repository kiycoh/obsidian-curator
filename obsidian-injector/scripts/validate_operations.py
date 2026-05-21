import argparse
import json
import os
import sys
from pathlib import Path

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"Error loading JSON from {path}: {e}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Validate operations JSON against distiller payloads")
    parser.add_argument("--operations", required=True, type=Path, help="Path to consolidated operations JSON file")
    parser.add_argument("--payload", required=True, action="append", dest="payloads", type=Path, help="Path to original payload JSON file(s) (can repeat)")
    parser.add_argument("--target", required=True, type=Path, help="Target folder in the vault")
    parser.add_argument("--out", required=True, type=Path, help="Output path for validated operations JSON")
    parser.add_argument("--rejected-out", type=Path, help="Output path for rejected operations JSON")
    args = parser.parse_args()

    # Load operations
    if not args.operations.exists():
        sys.stderr.write(f"Error: Operations file {args.operations} does not exist\n")
        sys.exit(1)
    
    operations_data = load_json(args.operations)
    if not isinstance(operations_data, dict) or "updates" not in operations_data:
        sys.stderr.write("Error: Operations JSON must contain a top-level 'updates' key containing a list of operations\n")
        sys.exit(1)
    
    ops = operations_data["updates"]
    if not isinstance(ops, list):
        sys.stderr.write("Error: 'updates' must be a JSON array\n")
        sys.exit(1)

    # Load and index all payloads
    valid_concepts = {} # source_basename -> set of concept names
    expected_collision_paths = {} # (source_basename, concept_name) -> path or None
    inbox_folders = set()

    for payload_path in args.payloads:
        if not payload_path.exists():
            sys.stderr.write(f"Error: Payload file {payload_path} does not exist\n")
            sys.exit(1)
        
        payload_data = load_json(payload_path)
        batches = payload_data.get("batches", [])
        for batch in batches:
            inbox_file = batch.get("inbox_file")
            if not inbox_file:
                continue
            
            source_basename = os.path.basename(inbox_file)
            inbox_dir = os.path.dirname(os.path.abspath(inbox_file))
            inbox_folders.add(inbox_dir)
            
            if source_basename not in valid_concepts:
                valid_concepts[source_basename] = set()
            
            concepts = batch.get("concepts", [])
            for c in concepts:
                name = c.get("name")
                if not name:
                    continue
                valid_concepts[source_basename].add(name)
                
                # Check collision path
                collision = c.get("vault_collision")
                if collision and isinstance(collision, dict) and collision.get("path"):
                    expected_collision_paths[(source_basename, name)] = collision["path"]
                else:
                    expected_collision_paths[(source_basename, name)] = None

    # Track results
    validated_ops = []
    rejected_ops = []

    target_dir_abs = os.path.abspath(args.target)

    for idx, op in enumerate(ops):
        heading = op.get("heading")
        op_type = op.get("op")
        source_basename = op.get("source_basename")
        path = op.get("path")
        
        # 1. Structural checks
        if not heading or not op_type:
            rejected_ops.append({
                "op": op,
                "reason": "Missing 'heading' or 'op' field"
            })
            continue

        if not source_basename:
            rejected_ops.append({
                "op": op,
                "reason": "Missing 'source_basename' field"
            })
            continue

        # 2. Source checks
        if source_basename not in valid_concepts:
            rejected_ops.append({
                "op": op,
                "reason": f"Unknown source_basename '{source_basename}' (not found in any loaded payloads)"
            })
            continue

        # 3. Concept validation
        if heading not in valid_concepts[source_basename]:
            rejected_ops.append({
                "op": op,
                "reason": f"Heading '{heading}' not present in payload concepts for source '{source_basename}'"
            })
            continue

        # 4. Check for forbidden path segments (like inbox folders or '/0 Inbox/')
        if path:
            path_abs = os.path.abspath(path)
            forbidden = False
            for folder in inbox_folders:
                if path_abs.startswith(folder):
                    forbidden = True
                    break
            if "/0 Inbox/" in path or "/0 inbox/" in path.lower() or forbidden:
                rejected_ops.append({
                    "op": op,
                    "reason": f"Target path '{path}' contains or points to a forbidden inbox directory segment"
                })
                continue

        # 5. Op-specific checks
        if op_type == "skip":
            # skips are clean but do not yield files to write/patch
            continue

        elif op_type == "patch":
            if not path:
                rejected_ops.append({
                    "op": op,
                    "reason": "Missing 'path' field for patch operation"
                })
                continue
            
            expected_path = expected_collision_paths.get((source_basename, heading))
            if not expected_path:
                rejected_ops.append({
                    "op": op,
                    "reason": f"Concept '{heading}' has no vault collision in the payload; cannot patch"
                })
                continue
                
            if os.path.abspath(path) != os.path.abspath(expected_path):
                rejected_ops.append({
                    "op": op,
                    "reason": f"Path '{path}' does not match expected collision path '{expected_path}'"
                })
                continue

            if not os.path.exists(path):
                rejected_ops.append({
                    "op": op,
                    "reason": f"Collision path '{path}' does not exist on disk"
                })
                continue

            validated_ops.append(op)

        elif op_type == "write":
            if not path:
                rejected_ops.append({
                    "op": op,
                    "reason": "Missing 'path' field for write operation"
                })
                continue
            
            path_abs = os.path.abspath(path)
            if not path_abs.startswith(target_dir_abs):
                rejected_ops.append({
                    "op": op,
                    "reason": f"Path '{path}' is not within the target folder '{target_dir_abs}'"
                })
                continue

            if os.path.exists(path):
                rejected_ops.append({
                    "op": op,
                    "reason": f"Target path '{path}' already exists on disk (should be a patch/enrich)"
                })
                continue

            validated_ops.append(op)

        else:
            rejected_ops.append({
                "op": op,
                "reason": f"Unknown operation type '{op_type}'"
            })

    # Save outputs
    # Write clean validated operations list directly (so bulk_writer accepts it)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(validated_ops, ensure_ascii=False, indent=2), encoding="utf-8")
    
    rejected_path = args.rejected_out if args.rejected_out else args.out.with_name(args.out.stem.replace("validated", "rejected") + ".json")
    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    rejected_path.write_text(json.dumps(rejected_ops, ensure_ascii=False, indent=2), encoding="utf-8")

    total_ops = len(ops)
    rejected_count = len(rejected_ops)
    rejection_rate = rejected_count / total_ops if total_ops > 0 else 0.0

    sys.stderr.write(
        f"[VALIDATOR] Processed {total_ops} operations. "
        f"Validated: {len(validated_ops)}. Rejected: {rejected_count} ({rejection_rate:.1%}).\n"
    )

    if rejection_rate >= 0.10:
        sys.stderr.write(f"[VALIDATOR] Fatal: Rejection rate {rejection_rate:.1%} is >= 10% threshold. Aborting batch.\n")
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
