from collections.abc import Sequence
from typing import TypeVar

import hou
from houkit.geomath import rotation_to
from houkit.models import Moject
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms

from .attributes import (
    Region,
    pedipalpcoxabuffer,
    pedipalpmembrane,
    pedipalpsegmentedge,
    pedipalpsegmentinset,
    pedipalpsegmentmid,
    pedipalpsegmentsupport,
)
from ..bases.attributes import basemaxillamembrane
from ..attributes import LegSegment, PedipalpSegment
from ..helper import points_from_geo, prims_by_attr, set_point_id
from ..legs.attributes import get_segment_sections
from ..legs.socket import get_front_coxa_socket_width
from .socket import get_pedipalp_socket_size
from ..segments.build import build_segment_bases
from ..segments.models import LimbAttributes, LimbParam


def build_basic(
    node: hou.SopNode,
) -> None:
    _, warnings = _build_segments(node)
    for w in warnings:
        node.addWarning(w)


def trim_bottom_side_length(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    m1, m3 = points_from_geo(
        geo,
        basemaxillamembrane(1),
        basemaxillamembrane(3),
    )
    v = m3.position() - m1.position()
    trim_length = hou.Vector3(v.x(), 0.0, v.z()).length()

    pedipalp_pts = _get_pedipalp_points(geo)
    prefix_start = pedipalpcoxabuffer(1, "start")
    prefix_support = pedipalpcoxabuffer(1, "support")
    for pt in pedipalp_pts:
        pid = pt.stringAttribValue("id")
        if pid.startswith(prefix_start) or pid.startswith(prefix_support):
            continue
        pos = pt.position()
        pt.setPosition(hou.Vector3(pos.x(), pos.y(), pos.z() + trim_length))


def position_basic(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    pedipalp_pts = _get_pedipalp_points(geo)
    top_right_pt, m1, m3, m4 = points_from_geo(
        geo,
        pedipalpcoxabuffer(1, "start", 3),
        basemaxillamembrane(1),
        basemaxillamembrane(3),
        basemaxillamembrane(4),
    )

    v = m3.position() - m1.position()
    direction = hou.Vector3(v.x(), 0.0, v.z()).normalized()
    q = rotation_to(hou.Vector3(0.0, 0.0, -1.0), direction)

    origin = m4.position() - q.rotate(top_right_pt.position())
    for pt in pedipalp_pts:
        pt.setPosition(q.rotate(pt.position()) + origin)


def _build_segments(
    node: hou.SopNode,
) -> Moject[tuple[list[list[hou.Point]], list[hou.Point], list[hou.Point]]]:
    geo = node.geometry()
    param = _get_pedipalp_param(node)
    attributes = _get_pedipalp_attributes()
    result = build_segment_bases(geo, param, attributes)
    (seg_tubes, thickness_pts, all_mem_pts), _ = result

    _attribute_pedipalp_coxa_buffers(1, seg_tubes[0][:8])

    return result


def _get_pedipalp_attributes(side: int = 1) -> LimbAttributes:
    return LimbAttributes(
        segment_region=Region.PEDIPALPSEGMENT,
        membrane_region=Region.PEDIPALPMEMBRANE,
        attribute_edge=lambda seg, d, c: pedipalpsegmentedge(side, seg, d, c),
        attribute_support=lambda seg, d, c: pedipalpsegmentsupport(side, seg, d, c),
        attribute_inset=lambda seg, d, c: pedipalpsegmentinset(side, seg, d, c),
        attribute_mid=lambda seg, m, c: pedipalpsegmentmid(side, seg, m, c),
        attribute_membrane=lambda jnt, l, c: pedipalpmembrane(side, jnt, l, c),
    )


def _attribute_pedipalp_coxa_buffers(
    side: int,
    coxa_pts: list[hou.Point],
) -> None:
    # Loop 0: start loop (to be pruned to start 3)
    for corner_offset, pt in enumerate(coxa_pts[0:4]):
        corner_idx = corner_offset + 1
        set_point_id(pt, pedipalpcoxabuffer(side, "start", corner_idx))

    # Loop 1: start support loop (to be deleted in delete_start_coxa_supports)
    for corner_offset, pt in enumerate(coxa_pts[4:8]):
        corner_idx = corner_offset + 1
        set_point_id(pt, pedipalpcoxabuffer(side, "support", corner_idx))


def _get_pedipalp_param(
    node: hou.SopNode,
) -> LimbParam:
    geo = node.geometry()
    pedipalp = get_parent(node)
    params = get_parms(pedipalp, use_tuple=False)

    legs = _get_legs_node(node)
    leg_params = get_parms(legs, use_tuple=False)
    control_params = get_parms(get_control(legs, "CONTROL"), use_tuple=False)

    base = pedipalp.input(0)
    front_leg_coxa_length = get_front_coxa_socket_width(base.geometry()) * leg_params.coxa_length_ratio
    pedipalp_coxa_length = front_leg_coxa_length * params.coxa_length
    socket_size = get_pedipalp_socket_size(geo)

    length_ratios = tuple(params.segment_length_ratios)
    segment_sections = _select_pedipalp_segments(get_segment_sections(legs))

    max_segment_yaws = _select_pedipalp_segments(tuple(leg_params.max_yaw_angles))[1:]
    min_segment_flexes = _select_pedipalp_segments(tuple(leg_params.min_flex_angles))[1:]

    param = LimbParam.from_specs(
        socket_size=socket_size,
        coxa_length=pedipalp_coxa_length,
        segment_sections=segment_sections,
        length_ratios=length_ratios,
        max_segment_yaws=max_segment_yaws,
        min_segment_flexes=min_segment_flexes,
        spine_ratio=control_params.segment_spine_ratio,
        joint_clearance_limits=tuple(control_params.joint_clearance_limits),
        support_loop_ratio=control_params.joint_support_loop_ratio,
        tarsus_wedge_angle=leg_params.tarsus_wedge_angle,
    )
    _lock_pedipalp_coxa_sections(param)
    return param


def _lock_pedipalp_coxa_sections(param: LimbParam) -> None:
    coxa_sections = (param.segment_sections[0][0], param.segment_sections[0][-1])
    param.segment_sections = (coxa_sections, *param.segment_sections[1:])


_T = TypeVar("_T")


def _select_pedipalp_segments(values: Sequence[_T]) -> tuple[_T, ...]:
    pedipalp_names = {segment.value for segment in PedipalpSegment}
    return tuple(
        value for segment, value in zip(LegSegment, values, strict=True)
        if segment.value in pedipalp_names
    )


def _get_pedipalp_points(
    geo: hou.Geometry,
) -> list[hou.Point]:
    pts = {
        pt
        for prim in prims_by_attr(
            geo,
            "region",
            (Region.PEDIPALPMEMBRANE, Region.PEDIPALPSEGMENT),
            startswith=True,
        )
        for pt in prim.points()
    }
    if not pts:
        raise ValueError("No pedipalp points found by region")
    return list(pts)


def _get_legs_node(node: hou.SopNode) -> hou.SopNode:
    legs = get_parent(node).input(1)
    assert legs is not None, "Expected legs as pedipalps input 1"
    return legs
