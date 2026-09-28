from collections.abc import Sequence

import hou
from houkit.attributer import add_prim_attrib

from ..helper import add_id_attr, set_point_id
from .models import LimbAttributes, LimbIdArgs


def attribute_segment_bases(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_pts: Sequence[hou.Point],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    """Attribute primitive regions and point IDs for a limb's segments, thickness, and membranes."""
    attribute_regions(geo, attributes, seg_pts, thickness_pts, mem_pts)
    attribute_points(geo, attributes, seg_pts, thickness_pts, mem_pts)


def attribute_regions(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_pts: Sequence[hou.Point],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    add_prim_attrib(geo, "region", "")

    mem_prims = {prim for pt in mem_pts for prim in pt.prims()}
    for prim in mem_prims:
        prim.setAttribValue("region", attributes.membrane_region)

    seg_prims = {prim for pt in (*seg_pts, *thickness_pts) for prim in pt.prims()} - mem_prims
    for prim in seg_prims:
        prim.setAttribValue("region", attributes.segment_region)


def attribute_points(
    geo: hou.Geometry,
    attributes: LimbAttributes,
    seg_pts: Sequence[hou.Point],
    thickness_pts: Sequence[hou.Point],
    mem_pts: Sequence[hou.Point],
) -> None:
    add_id_attr(geo)
    _attribute_segments(attributes, seg_pts)
    _attribute_thickness(attributes, thickness_pts)
    _attribute_membranes(attributes, mem_pts)


def _attribute_segments(
    attributes: LimbAttributes,
    seg_pts: Sequence[hou.Point],
) -> None:
    num_segs = len(seg_pts) // 16
    for seg_i in range(num_segs):
        seg_idx = seg_i + 1
        base = seg_i * 16
        for loop_offset, loop_idx in enumerate([2, 3, 4, 5]):
            loop_pts = seg_pts[base + loop_offset * 4 : base + (loop_offset + 1) * 4]
            for corner_offset, pt in enumerate(loop_pts):
                corner_idx = corner_offset + 1
                set_point_id(pt, attributes.segment_id(LimbIdArgs(seg_idx, loop_idx, corner_idx)))


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
            set_point_id(pt, attributes.segment_id(LimbIdArgs(former_seg, 6, corner_idx)))
        for corner_offset, pt in enumerate(latter_inset):
            corner_idx = corner_offset + 1
            set_point_id(pt, attributes.segment_id(LimbIdArgs(latter_seg, 1, corner_idx)))


def _attribute_membranes(
    attributes: LimbAttributes,
    mem_pts: Sequence[hou.Point],
) -> None:
    num_joints = len(mem_pts) // 12
    for joint_i in range(num_joints):
        joint_idx = joint_i + 1
        base = joint_i * 12
        for loop_offset, loop_idx in enumerate([1, 2, 3]):
            loop_pts = mem_pts[base + loop_offset * 4 : base + (loop_offset + 1) * 4]
            for corner_offset, pt in enumerate(loop_pts):
                corner_idx = corner_offset + 1
                set_point_id(pt, attributes.membrane_id(LimbIdArgs(joint_idx, loop_idx, corner_idx)))
