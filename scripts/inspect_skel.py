#!/usr/bin/env python
"""Inspects and diffs KineFX skeleton joints, local coordinate axes, and poses.

Features:
- Decomposes joint transforms (Matrix3) into local X (hinge), local Y (up), and local Z (aim).
- Measures elevation angles of rotation axes relative to the horizontal XZ plane.
- Checks chain planarity and measures out-of-plane distance across joint branches.
- Diffs posed vs rest skeletons (position displacement, local/world relative rotations, yaw deviation).
- Displays skeleton hierarchy tree.
"""

import argparse
import fnmatch
import math
import sys
import hou


def format_vec(v: hou.Vector3) -> str:
    return f"({v[0]:8.2f}, {v[1]:8.2f}, {v[2]:8.2f})"


def format_dir(v: hou.Vector3) -> str:
    return f"({v[0]:6.3f}, {v[1]:6.3f}, {v[2]:6.3f})"


def get_point_matrix3(pt: hou.Point) -> hou.Matrix3 | None:
    geo = pt.geometry()
    if geo.findPointAttrib("transform") is not None:
        return hou.Matrix3(pt.attribValue("transform"))
    return None


def get_point_matrix4(pt: hou.Point) -> hou.Matrix4:
    m3 = get_point_matrix3(pt) or hou.Matrix3(1.0)
    pos = pt.position()
    return hou.Matrix4((
        m3.at(0, 0), m3.at(0, 1), m3.at(0, 2), 0.0,
        m3.at(1, 0), m3.at(1, 1), m3.at(1, 2), 0.0,
        m3.at(2, 0), m3.at(2, 1), m3.at(2, 2), 0.0,
        pos.x(), pos.y(), pos.z(), 1.0,
    ))


def get_joint_points(geo: hou.Geometry, pattern: str | None = None) -> list[hou.Point]:
    if geo.findPointAttrib("name") is None:
        return []
    pts = geo.points()
    if pattern:
        return [p for p in pts if fnmatch.fnmatch(p.stringAttribValue("name"), pattern)]
    return list(pts)


def inspect_skeleton(
    hip_file: str,
    node_path: str,
    pattern: str | None = None,
    rest_path: str | None = None,
    show_axes: bool = True,
    show_planarity: bool = False,
    show_tree: bool = False,
    limit: int = 100,
) -> None:
    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Node not found at path '{node_path}' in '{hip_file}'")
        sys.exit(1)

    node.cook(force=True)
    geo = node.geometry()
    if geo is None:
        print(f"Error: Node '{node_path}' has no geometry.")
        sys.exit(1)

    matched_points = get_joint_points(geo, pattern)
    print(f"Node: {node.path()} [{hip_file}]")
    print(f"Total Points: {len(geo.points())} | Matched Joints: {len(matched_points)}")
    print("=" * 100)

    if not matched_points:
        print(f"No joints matching pattern '{pattern or '*'}' found on geometry.")
        return

    # 1. Pose Diff if rest_path is provided
    if rest_path:
        rest_node = hou.node(rest_path)
        if rest_node is None:
            print(f"Error: Rest skeleton node not found at path '{rest_path}'")
            sys.exit(1)
        rest_node.cook(force=True)
        rest_geo = rest_node.geometry()
        _print_pose_diff(geo, rest_geo, matched_points, limit)
        return

    # 2. Hierarchy Tree Display
    if show_tree:
        _print_hierarchy_tree(geo, matched_points)
        print("=" * 100)

    # 3. Joint & Axis Table
    if show_axes:
        _print_joint_table(geo, matched_points, limit)

    # 4. Planarity Analysis
    if show_planarity:
        _print_planarity_analysis(matched_points)


def _print_joint_table(geo: hou.Geometry, points: list[hou.Point], limit: int) -> None:
    has_parent = geo.findPointAttrib("parent_idx") is not None
    print(f"{'Joint Name':<26} {'Parent':<18} {'World Pos (P)':<30} {'Local X (Hinge)':<24} {'X Elev':<8} {'Local Z (Aim)':<24}")
    print("-" * 135)

    for pt in points[:limit]:
        name = pt.stringAttribValue("name") if geo.findPointAttrib("name") else f"pt_{pt.number()}"
        parent_name = "-"
        if has_parent:
            pidx = pt.attribValue("parent_idx")
            if pidx >= 0 and pidx < len(geo.points()):
                parent_pt = geo.point(pidx)
                parent_name = parent_pt.stringAttribValue("name") if geo.findPointAttrib("name") else f"pt_{pidx}"

        pos_str = format_vec(pt.position())
        m3 = get_point_matrix3(pt)
        if m3 is not None:
            axis_x = hou.Vector3(m3.at(0, 0), m3.at(0, 1), m3.at(0, 2))
            axis_z = hou.Vector3(m3.at(2, 0), m3.at(2, 1), m3.at(2, 2))
            elev_x = math.degrees(math.asin(max(-1.0, min(1.0, axis_x.y()))))
            x_str = format_dir(axis_x)
            z_str = format_dir(axis_z)
            elev_str = f"{elev_x:+.2f}°"
        else:
            x_str, z_str, elev_str = "n/a", "n/a", "n/a"

        print(f"{name:<26} {parent_name:<18} {pos_str:<30} {x_str:<24} {elev_str:<8} {z_str:<24}")

    if len(points) > limit:
        print(f"... and {len(points) - limit} more joints.")
    print("=" * 135)


def _print_hierarchy_tree(geo: hou.Geometry, points: list[hou.Point]) -> None:
    print("Hierarchy Tree:")
    has_parent = geo.findPointAttrib("parent_idx") is not None
    pts_set = set(points)

    children_map: dict[int, list[hou.Point]] = {}
    roots: list[hou.Point] = []

    for pt in points:
        pidx = pt.attribValue("parent_idx") if has_parent else -1
        if pidx < 0 or (has_parent and geo.point(pidx) not in pts_set):
            roots.append(pt)
        else:
            children_map.setdefault(pidx, []).append(pt)

    def _walk(pt: hou.Point, depth: int) -> None:
        indent = "  " * depth + "• "
        name = pt.stringAttribValue("name")
        pos = pt.position()
        print(f"{indent}{name}  {format_vec(pos)}")
        for ch in children_map.get(pt.number(), []):
            _walk(ch, depth + 1)

    for root in roots:
        _walk(root, 0)


def _print_planarity_analysis(points: list[hou.Point]) -> None:
    if len(points) < 3:
        print("Planarity check requires at least 3 points.")
        return

    # Derive reference plane from first two distinct points in XZ
    p0 = points[0].position()
    p1 = points[1].position()
    delta = p1 - p0
    dxz = hou.Vector3(delta.x(), 0.0, delta.z())
    if dxz.length() < 1e-6:
        # Fallback to endpoints
        delta = points[-1].position() - points[0].position()
        dxz = hou.Vector3(delta.x(), 0.0, delta.z())

    if dxz.length() < 1e-6:
        print("Cannot determine horizontal plane direction from points.")
        return

    dxz = dxz.normalized()
    plane_n = hou.Vector3(-dxz.z(), 0.0, dxz.x()).normalized()
    plane_d = plane_n.dot(p0)

    print(f"\nPlanarity Analysis (Reference Normal: {format_dir(plane_n)}):")
    max_dev = 0.0
    for pt in points:
        name = pt.stringAttribValue("name")
        dist = plane_n.dot(pt.position()) - plane_d
        dev = abs(dist)
        max_dev = max(max_dev, dev)
        print(f"  {name:<26}: distance to plane = {dist:+9.4f} mm")

    print("-" * 60)
    print(f"Max Out-of-Plane Deviation: {max_dev:.4f} mm")
    print("=" * 100)


def _print_pose_diff(geo: hou.Geometry, rest_geo: hou.Geometry, matched_points: list[hou.Point], limit: int) -> None:
    rest_pts_by_name = {p.stringAttribValue("name"): p for p in rest_geo.points() if rest_geo.findPointAttrib("name")}

    print(f"{'Joint Name':<26} {'Delta P (mm)':<14} {'Dist':<10} {'Local Rot (Euler Deg)':<28} {'World Rot (Euler Deg)':<28}")
    print("-" * 110)

    max_dist = 0.0
    for pt in matched_points[:limit]:
        name = pt.stringAttribValue("name")
        rest_pt = rest_pts_by_name.get(name)
        if rest_pt is None:
            continue

        p_posed = pt.position()
        p_rest = rest_pt.position()
        disp = p_posed - p_rest
        dist = disp.length()
        max_dist = max(max_dist, dist)

        m3_posed = get_point_matrix3(pt)
        m3_rest = get_point_matrix3(rest_pt)

        if m3_posed and m3_rest:
            m_local = m3_rest.inverted() * m3_posed
            m_world = m3_posed * m3_rest.inverted()
            rot_local = m_local.extractRotates()
            rot_world = m_world.extractRotates()
            loc_str = f"({rot_local[0]:6.1f}, {rot_local[1]:6.1f}, {rot_local[2]:6.1f})"
            wor_str = f"({rot_world[0]:6.1f}, {rot_world[1]:6.1f}, {rot_world[2]:6.1f})"
        else:
            loc_str, wor_str = "n/a", "n/a"

        disp_str = f"({disp.x():.1f}, {disp.y():.1f}, {disp.z():.1f})"
        print(f"{name:<26} {disp_str:<14} {dist:<10.3f} {loc_str:<28} {wor_str:<28}")

    print("-" * 110)
    print(f"Max Joint Displacement: {max_dist:.4f} mm")
    print("=" * 110)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect KineFX skeleton joints, axes, planarity, and pose diffs.")
    parser.add_argument("node_path", help="Path to SOP skeleton node")
    parser.add_argument("hip_file", nargs="?", default="test/test.hip", help="HIP file path (default: test/test.hip)")
    parser.add_argument("--hip", default=None, help="Alternative path to HIP file")
    parser.add_argument("-p", "--pattern", default=None, help="Glob pattern to filter joint names (e.g. '*leg_R1*')")
    parser.add_argument("--rest", default=None, help="Rest skeleton node path to diff against")
    parser.add_argument("--planarity", action="store_true", help="Analyze out-of-plane deviation and chain coplanarity")
    parser.add_argument("--tree", action="store_true", help="Display hierarchy tree view")
    parser.add_argument("--no-axes", action="store_true", help="Omit basis vectors table")
    parser.add_argument("--limit", type=int, default=100, help="Max joints to display (default: 100)")
    args = parser.parse_args()

    hip_path = args.hip or args.hip_file
    inspect_skeleton(
        hip_file=hip_path,
        node_path=args.node_path,
        pattern=args.pattern,
        rest_path=args.rest,
        show_axes=not args.no_axes,
        show_planarity=args.planarity,
        show_tree=args.tree,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
