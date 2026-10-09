from typing import Any

import hou
from houkit.attributer import add_prim_attrib, points_start_with
from houkit.geomath import rotation_to
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topology import points_to_positions

from ..bases.attributes import basecoxamemebrane, basecoxamembranemiddle
from ..helper import points_from_geo
from ..segments.build import build_segment_bases
from ..segments.models import LimbAttributes, LimbParam
from .attributes import (
    ID,
    Region,
    get_segment_sections,
    legmembrane,
    legsegmentedge,
    legsegmentinset,
    legsegmentmid,
    legsegmentsupport,
)
from .socket import get_front_coxa_socket_height, get_front_coxa_socket_width


def build_basic(
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
        _build_single_leg_basic(
            node,
            geo,
            params,
            control_params,
            front_socket_size,
            front_coxa_length,
            segment_sections,
            i,
        )


def position_basic(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    for i in range(4):
        _position_single_leg(geo, i + 1)


def _build_single_leg_basic(
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
    param = _get_leg_param(
        params,
        control_params,
        front_socket_size,
        front_coxa_length,
        segment_sections,
        leg_offset,
    )
    attributes = _get_leg_attributes(leg_idx)

    _, warnings = build_segment_bases(geo, param, attributes)
    for w in warnings:
        node.addWarning(w)


def _position_single_leg(
    geo: hou.Geometry,
    leg_idx: int,
) -> None:
    _, _, origin, direction = _get_leg_socket_frame(geo, leg_idx)
    q = rotation_to(hou.Vector3(0.0, 0.0, -1.0), direction)
    for pt in _get_leg_points(geo, leg_idx):
        pt.setPosition(q.rotate(pt.position()) + origin)


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
    origin_xz = top_mid + direction * bottom_z_offset

    p_u1, p_u2 = points_from_geo(
        geo,
        legsegmentedge(leg_idx, 1, 1, 4),
        legsegmentedge(leg_idx, 1, 1, 3),
    )
    leg_top_y = (p_u1.position().y() + p_u2.position().y()) / 2.0
    origin = hou.Vector3(origin_xz.x(), top_mid.y() - leg_top_y, origin_xz.z())
    return pts, mid_pts, origin, direction


def _get_leg_points(
    geo: hou.Geometry,
    leg_idx: int,
) -> list[hou.Point]:
    return points_start_with(geo, "id", (f"{ID.LEGSEGMENT}{leg_idx}", f"{ID.LEGMEMBRANE}{leg_idx}"))


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
        attribute_edge=lambda seg, d, c: legsegmentedge(leg_index, seg, d, c),
        attribute_support=lambda seg, d, c: legsegmentsupport(leg_index, seg, d, c),
        attribute_inset=lambda seg, d, c: legsegmentinset(leg_index, seg, d, c),
        attribute_mid=lambda seg, m, c: legsegmentmid(leg_index, seg, m, c),
        attribute_membrane=lambda jnt, l, c: legmembrane(leg_index, jnt, l, c),
    )
