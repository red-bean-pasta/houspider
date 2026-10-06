#!/usr/bin/env python
"""General geometry measurement tool for points, vectors, and edges.

Measures:
- Distances, horizontal reach (XZ), and elevation angle to the XZ plane.
- Angular relationships, dot products, and perpendicularity between two edges/vectors.
- Batches of point pairs.

Points can be specified by attribute 'id' (e.g. 'basesternummiddle1') or point number (e.g. '0' or '#0').
"""

import argparse
import math
import sys
import hou


def resolve_point(geo: hou.Geometry, spec: str, id_attrib: str = "id") -> hou.Point:
    """Resolves a point from an integer index (#0 or 0) or attribute value."""
    if spec.startswith("#") and spec[1:].isdigit():
        idx = int(spec[1:])
        pts = geo.points()
        if 0 <= idx < len(pts):
            return pts[idx]
        raise ValueError(f"Point index {idx} out of range (0..{len(pts)-1})")

    if spec.isdigit():
        idx = int(spec)
        pts = geo.points()
        if 0 <= idx < len(pts):
            return pts[idx]
        raise ValueError(f"Point index {idx} out of range (0..{len(pts)-1})")

    # Search by attribute
    if geo.findPointAttrib(id_attrib) is not None:
        for pt in geo.points():
            if pt.stringAttribValue(id_attrib) == spec:
                return pt

    raise ValueError(f"Could not resolve point '{spec}' (neither point index nor {id_attrib}='{spec}')")


def format_vec(v: hou.Vector3) -> str:
    return f"({v[0]:.3f}, {v[1]:.3f}, {v[2]:.3f})"


def vector_analysis(v: hou.Vector3) -> dict:
    l_3d = v.length()
    v_xz = hou.Vector3(v[0], 0.0, v[2])
    l_xz = v_xz.length()
    elev_deg = math.degrees(math.atan2(v[1], l_xz)) if l_3d > 1e-9 else 0.0
    return {
        "vector": v,
        "length_3d": l_3d,
        "length_xz": l_xz,
        "elevation_deg": elev_deg,
    }


def measure_single_edge(geo: hou.Geometry, p1_spec: str, p2_spec: str, id_attrib: str = "id") -> None:
    p1 = resolve_point(geo, p1_spec, id_attrib)
    p2 = resolve_point(geo, p2_spec, id_attrib)

    pos1 = p1.position()
    pos2 = p2.position()
    vec = pos2 - pos1
    info = vector_analysis(vec)

    print(f"Edge: {p1_spec} -> {p2_spec}")
    print(f"  Point 1: {format_vec(pos1)}")
    print(f"  Point 2: {format_vec(pos2)}")
    print(f"  Vector:  {format_vec(vec)}")
    print(f"  3D Length:         {info['length_3d']:.4f}")
    print(f"  XZ Length:         {info['length_xz']:.4f}")
    print(f"  Elevation to XZ:   {info['elevation_deg']:.2f}°")


def compare_two_edges(
    geo: hou.Geometry,
    edge1_specs: tuple[str, str],
    edge2_specs: tuple[str, str],
    id_attrib: str = "id",
) -> None:
    p1 = resolve_point(geo, edge1_specs[0], id_attrib)
    p2 = resolve_point(geo, edge1_specs[1], id_attrib)
    p3 = resolve_point(geo, edge2_specs[0], id_attrib)
    p4 = resolve_point(geo, edge2_specs[1], id_attrib)

    v1 = p2.position() - p1.position()
    v2 = p4.position() - p3.position()

    info1 = vector_analysis(v1)
    info2 = vector_analysis(v2)

    l1 = info1["length_3d"]
    l2 = info2["length_3d"]
    dot_3d = v1.dot(v2)
    cos_3d = max(-1.0, min(1.0, dot_3d / (l1 * l2))) if l1 > 1e-9 and l2 > 1e-9 else 0.0
    angle_3d = math.degrees(math.acos(cos_3d))

    v1_xz = hou.Vector3(v1[0], 0.0, v1[2])
    v2_xz = hou.Vector3(v2[0], 0.0, v2[2])
    l1_xz = v1_xz.length()
    l2_xz = v2_xz.length()
    dot_xz = v1_xz.dot(v2_xz)
    cos_xz = max(-1.0, min(1.0, dot_xz / (l1_xz * l2_xz))) if l1_xz > 1e-9 and l2_xz > 1e-9 else 0.0
    angle_xz = math.degrees(math.acos(cos_xz))

    ratio = l1 / l2 if l2 > 1e-9 else float("inf")

    print(f"Comparing Edge 1 vs Edge 2:")
    print(f"  Edge 1: ({edge1_specs[0]} -> {edge1_specs[1]})")
    print(f"    Vector: {format_vec(v1)} | Len 3D: {l1:.4f} | Len XZ: {l1_xz:.4f} | Elev: {info1['elevation_deg']:.2f}°")
    print(f"  Edge 2: ({edge2_specs[0]} -> {edge2_specs[1]})")
    print(f"    Vector: {format_vec(v2)} | Len 3D: {l2:.4f} | Len XZ: {l2_xz:.4f} | Elev: {info2['elevation_deg']:.2f}°")
    print("-" * 70)
    print(f"  Length Ratio (E1 / E2): {ratio:.4f}")
    print(f"  3D Dot Product:         {dot_3d:.4f} (normalized: {cos_3d:.4f})")
    print(f"  3D Angle:               {angle_3d:.2f}°")
    print(f"  XZ Dot Product:         {dot_xz:.4f} (normalized: {cos_xz:.4f})")
    print(f"  XZ Angle:               {angle_xz:.2f}° (perpendicularity deviation: {abs(90.0 - angle_xz):.2f}°)")


def measure_batch_pairs(geo: hou.Geometry, pairs: list[str], id_attrib: str = "id") -> None:
    print("-" * 80)
    print(f"{'Pair':<32} {'3D Len':<10} {'XZ Len':<10} {'Elev (°)':<10} {'Vector':<24}")
    print("-" * 80)
    for pair in pairs:
        tokens = [t.strip() for t in pair.split(",") if t.strip()]
        if len(tokens) != 2:
            print(f"Skipping invalid pair '{pair}' (expected 'pt1,pt2')")
            continue
        try:
            p1 = resolve_point(geo, tokens[0], id_attrib)
            p2 = resolve_point(geo, tokens[1], id_attrib)
            vec = p2.position() - p1.position()
            info = vector_analysis(vec)
            name = f"{tokens[0]} -> {tokens[1]}"
            print(f"{name:<32} {info['length_3d']:<10.3f} {info['length_xz']:<10.3f} {info['elevation_deg']:<10.2f} {format_vec(vec):<24}")
        except Exception as e:
            print(f"{pair:<32} Error: {e}")
    print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure geometry distances, vectors, and angles.")
    parser.add_argument("node_path", help="Path to SOP node")
    parser.add_argument("--hip", default="test/test.hip", help="Path to .hip file (default: test/test.hip)")
    parser.add_argument("--attrib", default="id", help="Point ID attribute name (default: 'id')")
    parser.add_argument("-p", "--points", nargs=2, metavar=("P1", "P2"), help="Measure vector from P1 to P2")
    parser.add_argument("--edge1", nargs=2, metavar=("P1", "P2"), help="First edge for comparison")
    parser.add_argument("--edge2", nargs=2, metavar=("P3", "P4"), help="Second edge for comparison")
    parser.add_argument("--pairs", nargs="+", help="List of 'P1,P2' pairs to measure in batch")
    args = parser.parse_args()

    hou.hipFile.load(args.hip)
    node = hou.node(args.node_path)
    if node is None:
        print(f"Error: Node not found at path '{args.node_path}'")
        sys.exit(1)

    node.cook(force=True)
    geo = node.geometry()
    if geo is None:
        print(f"Error: Node '{args.node_path}' has no geometry.")
        sys.exit(1)

    print(f"Node: {node.path()} ({len(geo.points())} pts, {len(geo.prims())} prims)")
    print("=" * 70)

    if args.edge1 and args.edge2:
        compare_two_edges(geo, tuple(args.edge1), tuple(args.edge2), args.attrib)
    elif args.points:
        measure_single_edge(geo, args.points[0], args.points[1], args.attrib)
    elif args.pairs:
        measure_batch_pairs(geo, args.pairs, args.attrib)
    else:
        print("Specify -p P1 P2, --edge1 P1 P2 --edge2 P3 P4, or --pairs P1,P2 P3,P4 ...")


if __name__ == "__main__":
    main()
