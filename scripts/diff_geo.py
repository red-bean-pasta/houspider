#!/usr/bin/env python
"""Compares geometry between two SOP nodes (or a node and its input node).

Reports added/removed points, point displacements, and attribute changes.
"""

import argparse
import sys
import hou


def diff_geo(
    hip_file: str,
    node_path: str,
    ref_path: str | None = None,
    id_attrib: str = "id",
    min_dist: float = 1e-5,
    limit: int = 50,
) -> None:
    hou.hipFile.load(hip_file)
    node = hou.node(node_path)
    if node is None:
        print(f"Error: Target node not found at '{node_path}'")
        sys.exit(1)

    if ref_path:
        ref_node = hou.node(ref_path)
        if ref_node is None:
            print(f"Error: Reference node not found at '{ref_path}'")
            sys.exit(1)
    else:
        inputs = node.inputs()
        if not inputs or inputs[0] is None:
            print(f"Error: Node '{node_path}' has no input node. Specify reference with --ref.")
            sys.exit(1)
        ref_node = inputs[0]

    node.cook(force=True)
    ref_node.cook(force=True)

    geo = node.geometry()
    ref_geo = ref_node.geometry()

    print(f"Comparing:")
    print(f"  Reference (A): {ref_node.path()} ({len(ref_geo.points())} pts, {len(ref_geo.prims())} prims)")
    print(f"  Target    (B): {node.path()} ({len(geo.points())} pts, {len(geo.prims())} prims)")
    print("=" * 80)

    # Attribute difference
    ref_pt_attrs = {a.name() for a in ref_geo.pointAttribs()}
    cur_pt_attrs = {a.name() for a in geo.pointAttribs()}
    new_attrs = cur_pt_attrs - ref_pt_attrs
    del_attrs = ref_pt_attrs - cur_pt_attrs
    if new_attrs:
        print(f"Added point attributes: {sorted(new_attrs)}")
    if del_attrs:
        print(f"Removed point attributes: {sorted(del_attrs)}")

    # Point matching: prefer id_attrib if present on both
    use_id = (
        id_attrib
        and ref_geo.findPointAttrib(id_attrib) is not None
        and geo.findPointAttrib(id_attrib) is not None
    )

    if use_id:
        ref_pts = {
            p.stringAttribValue(id_attrib): p
            for p in ref_geo.points()
            if p.stringAttribValue(id_attrib)
        }
        cur_pts = {
            p.stringAttribValue(id_attrib): p
            for p in geo.points()
            if p.stringAttribValue(id_attrib)
        }

        added_ids = sorted(set(cur_pts) - set(ref_pts))
        removed_ids = sorted(set(ref_pts) - set(cur_pts))
        common_ids = sorted(set(cur_pts) & set(ref_pts))

        moved = []
        for pid in common_ids:
            p_ref = ref_pts[pid]
            p_cur = cur_pts[pid]
            disp = p_cur.position() - p_ref.position()
            dist = disp.length()
            if dist >= min_dist:
                moved.append((pid, p_ref.position(), p_cur.position(), disp, dist))

        print(f"Point ID matching on '{id_attrib}':")
        print(f"  Common named points: {len(common_ids)}")
        print(f"  Added named points:   {len(added_ids)}")
        print(f"  Removed named points: {len(removed_ids)}")
        print(f"  Points moved (>= {min_dist}): {len(moved)}")

        if added_ids:
            shown = added_ids[:10]
            extra = f" (and {len(added_ids) - 10} more)" if len(added_ids) > 10 else ""
            print(f"  Sample added IDs: {', '.join(shown)}{extra}")

        if removed_ids:
            shown = removed_ids[:10]
            extra = f" (and {len(removed_ids) - 10} more)" if len(removed_ids) > 10 else ""
            print(f"  Sample removed IDs: {', '.join(shown)}{extra}")

    else:
        # Fall back to point number matching
        min_pts = min(len(ref_geo.points()), len(geo.points()))
        moved = []
        for i in range(min_pts):
            p_ref = ref_geo.iterPoints()[i]
            p_cur = geo.iterPoints()[i]
            disp = p_cur.position() - p_ref.position()
            dist = disp.length()
            if dist >= min_dist:
                pid = f"#{i}"
                moved.append((pid, p_ref.position(), p_cur.position(), disp, dist))

        print(f"Point index matching (no unique '{id_attrib}' attrib):")
        print(f"  Points moved (>= {min_dist}): {len(moved)}")

    if moved:
        moved.sort(key=lambda item: item[4], reverse=True)
        max_dist = moved[0][4]
        avg_dist = sum(item[4] for item in moved) / len(moved)
        print(f"  Displacement: max={max_dist:.4f}, avg={avg_dist:.4f}")
        print("-" * 80)
        print(f"{'Point ID / #':<24} {'Ref Pos':<24} {'Target Pos':<24} {'Dist':<10}")
        print("-" * 80)
        for pid, pos_a, pos_b, disp, dist in moved[:limit]:
            str_a = f"({pos_a[0]:.2f}, {pos_a[1]:.2f}, {pos_a[2]:.2f})"
            str_b = f"({pos_b[0]:.2f}, {pos_b[1]:.2f}, {pos_b[2]:.2f})"
            print(f"{pid:<24} {str_a:<24} {str_b:<24} {dist:<10.3f}")
        if len(moved) > limit:
            print(f"... and {len(moved) - limit} more points.")
    else:
        print("  No point displacement detected above threshold.")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff geometry between two SOP nodes.")
    parser.add_argument("node_path", help="Target SOP node path")
    parser.add_argument("--ref", help="Reference SOP node path (defaults to target node's first input)")
    parser.add_argument("--hip", default="test/test.hip", help="HIP file path (default: test/test.hip)")
    parser.add_argument("--attrib", default="id", help="Point ID attribute name (default: 'id')")
    parser.add_argument("--min-dist", type=float, default=1e-5, help="Minimum distance threshold (default: 1e-5)")
    parser.add_argument("--limit", type=int, default=50, help="Max points to list (default: 50)")
    args = parser.parse_args()

    diff_geo(args.hip, args.node_path, args.ref, args.attrib, args.min_dist, args.limit)


if __name__ == "__main__":
    main()
