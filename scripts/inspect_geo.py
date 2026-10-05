#!/usr/bin/env python
"""Inspects geometry points, primitives, and attributes for a specified node in a HIP file."""

import argparse
import sys
import hou


def inspect_geo(
    hip_file: str,
    node_path: str,
    attrib_name: str | None = None,
    value_filter: str | None = None,
    target_type: str = "point",
    limit: int = 50,
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

    if target_type == "point":
        elements = geo.points()
        attribs = [a.name() for a in geo.pointAttribs()]
    else:
        elements = geo.prims()
        attribs = [a.name() for a in geo.primAttribs()]

    print(f"Available {target_type} attributes: {attribs}\n")

    filtered = []
    for elem in elements:
        if attrib_name:
            if not elem.geometry().findPointAttrib(attrib_name) if target_type == "point" else not elem.geometry().findPrimAttrib(attrib_name):
                continue
            val = elem.attribValue(attrib_name)
            if value_filter is not None and str(val) != str(value_filter):
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
    parser.add_argument("node_path", help="Path to Houdini node (e.g. /obj/spider/generator/prosoma/base)")
    parser.add_argument("--hip", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("--attrib", help="Attribute name to inspect / filter by")
    parser.add_argument("--value", help="Value to match for the specified attribute")
    parser.add_argument("--type", choices=["point", "prim"], default="point", help="Target element type (point or prim)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of items to display")
    args = parser.parse_args()

    inspect_geo(args.hip, args.node_path, args.attrib, args.value, args.type, args.limit)


if __name__ == "__main__":
    main()
