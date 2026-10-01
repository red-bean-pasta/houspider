from typing import Any

import hou
from houkit.attributer import add_prim_attrib
from houkit.geomath import rotation_to
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topology import points_to_positions

from ..bases.attributes import basecoxamemebrane, basecoxamembranemiddle
from ..helper import points_from_geo
from ..segments.build import build_segment_bases
from ..segments.models import LimbAttributes, LimbParam
from .attributes import Region, get_segment_sections, legmembrane, legsegment
from .coxa import adjust_coxa, attribute_coxa_buffer
from .socket import get_front_coxa_socket_height, get_front_coxa_socket_width


def extrude_legs(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    add_prim_attrib(geo, "region", "")

    parent = get_parent(node)
    params = get_parms(parent, use_tuple=False)
    control_params = get_parms(get_control(parent, "CONTROL"), use_tuple=False)

    front_socket_size = (get_front_coxa_socket_width(geo), get_front_coxa_socket_height(geo))
    front_coxa_length = front_socket_size[0] * params.coxa_length_ratio
    segment_sections = get_segment_sections(parent)

    for i in range(4):
        _extrude_single_leg(
            node,
            geo,
            params,
            control_params,
            front_socket_size,
            front_coxa_length,
            segment_sections,
            i,
        )


def _extrude_single_leg(
    node: hou.SopNode,
    geo: hou.Geometry,
    params: Any,
    control_params: Any,
    front_socket_size: tuple[float, float],
    front_coxa_length: float,
    segment_sections: tuple[tuple[tuple[float, float, float], ...], ...],
    leg_offset: int,
) -> None:
    leg_idx = leg_offset + 1
    pts, mid_pts, origin, direction = _get_leg_socket_frame(geo, leg_idx)

    param = _get_leg_param(
        params,
        control_params,
        front_socket_size,
        front_coxa_length,
        segment_sections,
        leg_offset,
    )
    attributes = _get_leg_attributes(leg_idx)

    (seg_pts, thickness_pts, mem_pts), warnings = build_segment_bases(geo, param, attributes)
    for w in warnings:
        node.addWarning(w)

    _orient_leg_points(seg_pts + thickness_pts + mem_pts, origin, direction)

    buffer_loop, pentagon_pts = adjust_coxa(node, pts, mid_pts, seg_pts[:16])
    attribute_coxa_buffer(leg_idx, buffer_loop, pentagon_pts)


def _get_leg_socket_frame(
    geo: hou.Geometry,
    leg_idx: int,
) -> tuple[list[hou.Point], list[hou.Point], hou.Vector3, hou.Vector3]:
    pts = list(
        points_from_geo(
            geo,
            basecoxamemebrane(leg_idx, 4),
            basecoxamemebrane(leg_idx, 3),
            basecoxamemebrane(leg_idx, 1),
            basecoxamemebrane(leg_idx, 2),
        )
    )
    mid_pts = list(
        points_from_geo(
            geo,
            basecoxamembranemiddle(leg_idx, 2),
            basecoxamembranemiddle(leg_idx, 1),
        )
    )

    pos_top_sz, pos_top_bz, pos_btm_sz, pos_btm_bz = points_to_positions(pts)
    top_mid = (pos_top_sz + pos_top_bz) / 2.0
    btm_mid = (pos_btm_sz + pos_btm_bz) / 2.0
    direction = hou.Vector3(top_mid.x() - btm_mid.x(), 0.0, top_mid.z() - btm_mid.z()).normalized()
    bottom_z_offset = (btm_mid - top_mid).dot(direction)
    origin = top_mid + direction * bottom_z_offset
    return pts, mid_pts, origin, direction


def _orient_leg_points(
    points: list[hou.Point],
    origin: hou.Vector3,
    direction: hou.Vector3,
) -> None:
    q = rotation_to(hou.Vector3(0.0, 0.0, -1.0), direction)
    for pt in points:
        pt.setPosition(q.rotate(pt.position()) + origin)


def _get_leg_param(
    params: Any,
    control_params: Any,
    front_socket_size: tuple[float, float],
    front_coxa_length: float,
    segment_sections: tuple[tuple[tuple[float, float, float], ...], ...],
    leg_index: int,
) -> LimbParam:
    width_ratio = 1.0 if leg_index == 0 else params.leg_width_ratios[leg_index - 1]
    length_ratio = 1.0 if leg_index == 0 else params.leg_length_ratios[leg_index - 1]
    front_w, front_h = front_socket_size

    return LimbParam.from_specs(
        socket_size=(front_w * width_ratio, front_h * width_ratio),
        coxa_length=front_coxa_length * length_ratio,
        segment_sections=segment_sections,
        length_ratios=tuple(params.segment_length_ratios),
        max_segment_yaws=tuple(params.max_yaw_angles)[1:],
        min_segment_flexes=tuple(params.min_flex_angles)[1:],
        spine_ratio=control_params.segment_spine_ratio,
        joint_clearance_limits=tuple(control_params.joint_clearance_limits),
        support_loop_ratio=control_params.joint_support_loop_ratio,
        tarsus_wedge_angle=params.tarsus_wedge_angle,
    )


def _get_leg_attributes(leg_index: int) -> LimbAttributes:
    return LimbAttributes(
        segment_region=Region.LEGSEGMENT,
        membrane_region=Region.LEGMEMBRANE,
        segment_id=lambda a: legsegment(leg_index, *a),
        membrane_id=lambda a: legmembrane(leg_index, *a),
    )
