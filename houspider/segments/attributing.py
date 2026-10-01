from collections.abc import Sequence

import hou
from houkit.attributer import add_prim_attrib

from ..helper import add_id_attr, set_point_id
from .models import LimbAttributes


def attribute_segment_bases(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_tubes: list[list[hou.Point]],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    """Attribute primitive regions and point IDs for a limb's segments, thickness, and membranes."""
    attribute_regions(geo, attributes, seg_tubes, thickness_pts, mem_pts)
    attribute_points(geo, attributes, seg_tubes, thickness_pts, mem_pts)


def attribute_regions(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_tubes: list[list[hou.Point]],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    add_prim_attrib(geo, "region", "")

    mem_prims = {prim for pt in mem_pts for prim in pt.prims()}
    for prim in mem_prims:
        prim.setAttribValue("region", attributes.membrane_region)

    all_seg_pts = [pt for seg in seg_tubes for pt in seg]
    seg_prims = {prim for pt in (*all_seg_pts, *thickness_pts) for prim in pt.prims()} - mem_prims
    for prim in seg_prims:
        prim.setAttribValue("region", attributes.segment_region)


def attribute_points(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_tubes: list[list[hou.Point]],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    add_id_attr(geo)
    _attribute_segments(attributes, seg_tubes)
    _attribute_thickness(attributes, thickness_pts)
    _attribute_membranes(attributes, mem_pts)


def _attribute_segments(
    attributes: LimbAttributes,
    seg_tubes: list[list[hou.Point]],
) -> None:
    for seg_i, seg_pts in enumerate(seg_tubes):
        seg_idx = seg_i + 1
        num_loops = len(seg_pts) // 4
        assert num_loops >= 4, f"Expected at least 4 loops for segment {seg_idx}, got {num_loops}"

        # Loop 0: edge_1
        for corner_offset, pt in enumerate(seg_pts[:4]):
            set_point_id(pt, attributes.attribute_edge(seg_idx, 1, corner_offset + 1))

        # Loop 1: support_1
        for corner_offset, pt in enumerate(seg_pts[4:8]):
            set_point_id(pt, attributes.attribute_support(seg_idx, 1, corner_offset + 1))

        # Intermediate loops (if any)
        num_mid_loops = num_loops - 4
        for mid_i in range(num_mid_loops):
            mid_pts = seg_pts[(2 + mid_i) * 4 : (3 + mid_i) * 4]
            for corner_offset, pt in enumerate(mid_pts):
                set_point_id(pt, attributes.attribute_mid(seg_idx, mid_i + 1, corner_offset + 1))

        # Penultimate loop: support_-1
        for corner_offset, pt in enumerate(seg_pts[-8:-4]):
            set_point_id(pt, attributes.attribute_support(seg_idx, -1, corner_offset + 1))

        # Last loop: edge_-1
        for corner_offset, pt in enumerate(seg_pts[-4:]):
            set_point_id(pt, attributes.attribute_edge(seg_idx, -1, corner_offset + 1))


def _attribute_thickness(
    attributes: LimbAttributes,
    thickness_pts: Sequence[hou.Point],
) -> None:
    num_joints = len(thickness_pts) // 8
    for joint_i in range(num_joints):
        former_seg = joint_i + 1
        latter_seg = joint_i + 2
        base = joint_i * 8
        former_inset = thickness_pts[base : base + 4]
        latter_inset = thickness_pts[base + 4 : base + 8]
        for corner_offset, pt in enumerate(former_inset):
            corner_idx = corner_offset + 1
            set_point_id(pt, attributes.attribute_inset(former_seg, -1, corner_idx))
        for corner_offset, pt in enumerate(latter_inset):
            corner_idx = corner_offset + 1
            set_point_id(pt, attributes.attribute_inset(latter_seg, 1, corner_idx))


def _attribute_membranes(
    attributes: LimbAttributes,
    mem_pts: Sequence[hou.Point],
) -> None:
    num_joints = len(mem_pts) // 12
    for joint_i in range(num_joints):
        joint_idx = joint_i + 1
        base = joint_i * 12
        for loop_offset, loop_idx in enumerate([1, "mid", -1]):
            loop_pts = mem_pts[base + loop_offset * 4 : base + (loop_offset + 1) * 4]
            for corner_offset, pt in enumerate(loop_pts):
                corner_idx = corner_offset + 1
                set_point_id(pt, attributes.attribute_membrane(joint_idx, loop_idx, corner_idx))
