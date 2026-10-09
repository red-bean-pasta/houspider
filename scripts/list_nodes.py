#!/usr/bin/env python
"""Lists, searches, and inspects nodes in a Houdini HIP file."""

import argparse
import fnmatch
import sys
import hou


def list_nodes(
    hip_file: str,
    root_path: str = "/obj",
    pattern: str | None = None,
    type_filter: str | None = None,
    recursive: bool = False,
    show_inputs: bool = False,
) -> None:
    hou.hipFile.load(hip_file)
    root_node = hou.node(root_path)
    if root_node is None:
        print(f"Error: Node not found at path '{root_path}'")
        sys.exit(1)

    nodes = list(root_node.allSubChildren()) if recursive else list(root_node.children())

    matched = []
    for node in nodes:
        if pattern:
            name_match = fnmatch.fnmatch(node.name(), pattern)
            path_match = fnmatch.fnmatch(node.path(), pattern)
            if not (name_match or path_match):
                continue
        if type_filter:
            type_name = node.type().name().lower()
            if type_filter.lower() not in type_name:
                continue
        matched.append(node)

    mode_label = "descendants" if recursive else "children"
    print(f"Nodes under '{root_path}' ({mode_label}): {len(matched)} matched / {len(nodes)} total\n")

    for node in matched:
        type_str = node.type().name()
        line = f"  {node.path()} [{type_str}]"
        if show_inputs:
            inputs = [inp.path() if inp else "None" for inp in node.inputs()]
            line += f" (inputs: {', '.join(inputs)})"
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="List and filter nodes in a HIP file.")
    parser.add_argument("hip_file", nargs="?", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("--root", default="/obj", help="Root or parent node path (default: /obj)")
    parser.add_argument("-p", "--pattern", help="Filter node names or paths by glob pattern (e.g. '*leg*')")
    parser.add_argument("-t", "--type", dest="type_filter", help="Filter by node type (e.g. 'null', 'subnet', 'python')")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively inspect all sub-children")
    parser.add_argument("--inputs", action="store_true", help="Show input node connections")
    args = parser.parse_args()

    list_nodes(
        args.hip_file,
        root_path=args.root,
        pattern=args.pattern,
        type_filter=args.type_filter,
        recursive=args.recursive,
        show_inputs=args.inputs,
    )


if __name__ == "__main__":
    main()
