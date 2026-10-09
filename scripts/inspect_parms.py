#!/usr/bin/env python
"""Inspects parameters, values, and controls on a Houdini node in a HIP file."""

import argparse
import fnmatch
import sys
import hou


def inspect_parms(
    hip_file: str,
    node_path: str,
    pattern: str | None = None,
    only_modified: bool = False,
) -> None:
    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Node not found at path '{node_path}'")
        sys.exit(1)

    parm_tuples = node.parmTuples()
    print(f"Node: {node.path()} [{node.type().name()}]")
    print(f"Total Parameters: {len(parm_tuples)}\n")

    matched = []
    for pt in parm_tuples:
        name = pt.name()
        label = pt.description()

        if pattern:
            name_match = fnmatch.fnmatch(name, pattern)
            label_match = fnmatch.fnmatch(label, pattern)
            if not (name_match or label_match):
                continue

        # Check if modified from default
        try:
            is_default = pt.isAtDefault()
        except Exception:
            is_default = True

        if only_modified and is_default:
            continue

        matched.append((pt, is_default))

    if not matched:
        print("No matching parameters found.")
        return

    print(f"{'Parameter':<28} {'Label':<26} {'Value':<30} {'Default?'}")
    print("-" * 92)

    for pt, is_default in matched:
        name = pt.name()
        label = pt.description()
        try:
            val = pt.eval()
            if len(pt) == 1:
                val_str = str(val[0])
            else:
                val_str = str(tuple(val))
        except Exception as exc:
            val_str = f"<Error: {exc}>"

        default_str = "yes" if is_default else "MODIFIED"
        print(f"{name:<28} {label:<26} {val_str:<30} {default_str}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect node parameters in a Houdini HIP file.")
    parser.add_argument("node_path", help="Path to node (e.g. /obj/spider/geometry/legs/CONTROL)")
    parser.add_argument("hip_file", nargs="?", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("-p", "--pattern", help="Filter parameter names or labels by glob (e.g. '*wedge*', '*ratio*')")
    parser.add_argument("-m", "--modified", action="store_true", help="Only show parameters modified from their defaults")
    args = parser.parse_args()

    inspect_parms(
        args.hip_file,
        args.node_path,
        pattern=args.pattern,
        only_modified=args.modified,
    )


if __name__ == "__main__":
    main()
