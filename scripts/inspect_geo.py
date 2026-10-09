#!/usr/bin/env python
"""Inspects geometry points, primitives, and attributes for a specified node in a HIP file."""

import argparse
from collections import Counter
import fnmatch
import sys
import hou


def inspect_geo(
    hip_file: str,
    node_path: str,
    attrib_name: str | None = None,
    value_filter: str | None = None,
    target_type: str = "point",
    limit: int = 50,
    show_unique: bool = False,
) -> None:
    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Node not found at path '{node_path}'")
        sys.exit(1)

    node.cook(force=True)
    geo = node.geometry()
    if geo is None:
        print(f"Error: Node '{node_path}' has no geometry.")
        sys.exit(1)

    print(f"Node: {node.path()}")
    print(f"Total Points: {len(geo.points())}, Total Primitives: {len(geo.prims())}")

    has_attrib = (geo.findPointAttrib if target_type == "point" else geo.findPrimAttrib)
    elements = geo.points() if target_type == "point" else geo.prims()
    attribs = [a.name() for a in (geo.pointAttribs() if target_type == "point" else geo.primAttribs())]

    print(f"Available {target_type} attributes: {attribs}\n")

    if show_unique and attrib_name:
        if not has_attrib(attrib_name):
            print(f"Error: Attribute '{attrib_name}' not found on {target_type}s.")
            sys.exit(1)
        counts = Counter(elem.attribValue(attrib_name) for elem in elements)
        print(f"Unique values for '{attrib_name}' ({len(counts)} distinct):\n")
        for val, count in sorted(counts.items(), key=lambda x: str(x[0])):
            print(f"  {val!r} (count: {count})")
        return

    filtered = []
    is_glob = value_filter is not None and any(c in value_filter for c in ("*", "?", "["))
    for elem in elements:
        if attrib_name:
            if not has_attrib(attrib_name):
                continue
            val = elem.attribValue(attrib_name)
            if value_filter is not None:
                str_val = str(val)
                if is_glob:
                    if not fnmatch.fnmatch(str_val, value_filter):
                        continue
                elif str_val != str(value_filter):
                    continue
        filtered.append(elem)

    print(f"Matching {target_type}s: {len(filtered)} (showing up to {limit})")
    for elem in filtered[:limit]:
        info = [f"#{elem.number()}"]
        if target_type == "point":
            pos = elem.position()
            info.append(f"pos=({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
        if attrib_name:
            info.append(f"{attrib_name}={elem.attribValue(attrib_name)!r}")
        else:
            for a in attribs[:5]:
                info.append(f"{a}={elem.attribValue(a)!r}")
        print("  " + " | ".join(info))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Houdini geometry attributes.")
    parser.add_argument("node_path", help="Path to Houdini node (e.g. /obj/spider/geometry/legs/OUT_LEGS)")
    parser.add_argument("--hip", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("--attrib", help="Attribute name to inspect / filter by")
    parser.add_argument("--value", help="Value or glob pattern (e.g. 'legsegment1_1*') to match for attribute")
    parser.add_argument("-u", "--unique", action="store_true", help="List all distinct values and occurrence counts for the attribute")
    parser.add_argument("--type", choices=["point", "prim"], default="point", help="Target element type (point or prim)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of items to display")
    args = parser.parse_args()

    inspect_geo(
        args.hip,
        args.node_path,
        args.attrib,
        args.value,
        args.type,
        args.limit,
        show_unique=args.unique,
    )


if __name__ == "__main__":
    main()
