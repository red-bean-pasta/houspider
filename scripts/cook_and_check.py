#!/usr/bin/env python
"""Cooks nodes in a Houdini HIP file and reports any cooking errors."""

import argparse
import sys
import hou


def cook_and_check(hip_file: str, root_path: str = "/obj") -> bool:
    print(f"Loading HIP: {hip_file}")
    hou.hipFile.load(hip_file)

    target_node = hou.node(root_path)
    if target_node is None:
        print(f"Error: Node not found at path '{root_path}'")
        return False

    nodes_to_cook = [target_node] + list(target_node.allSubChildren())
    print(f"Cooking {len(nodes_to_cook)} nodes under '{root_path}'...")

    for node in nodes_to_cook:
        try:
            node.cook(force=True)
        except hou.Error as exc:
            print(f"\nFAILED: {node.path()}")
            errors = node.errors()
            if errors:
                for err in errors:
                    print(f"  ERROR: {err}")
            else:
                print(f"  ERROR: {exc}")
            return False

    print("All nodes cooked successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Cook and check Houdini HIP file nodes.")
    parser.add_argument("hip_file", nargs="?", default="test/test.hip", help="Path to .hip file")
    parser.add_argument("--root", default="/obj", help="Root node path to cook under (default: /obj)")
    args = parser.parse_args()

    success = cook_and_check(args.hip_file, args.root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
