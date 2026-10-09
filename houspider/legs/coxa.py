import math

import hou
from houkit.attributer import unique_points_by_attrib
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topology import fill_face, fill_pentagon_with_buffer, points_to_positions

from ..bases.attributes import basecoxamemebrane, basecoxamembranemiddle
from ..helper import points_from_geo, set_point_id
from ..segments.helper import compute_intermediate_ratios, update_intermediate_positions
from .attributes import (
    legsegmentbuffer,
    legsegmentedge,
    legsegmentinset,
    legsegmentmid,
    legsegmentsupport,
)


def adjust_coxa_start(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    control_params = get_parms(get_control(get_parent(node), "CONTROL"), use_tuple=False)
    wedge_angle = control_params.coxa_start_wedge_angle
    for i in range(4):
        _adjust_single_coxa_start(geo, i + 1, wedge_angle)


def fill_coxa_upper_pentagon(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    for i in range(4):
        leg_idx = i + 1
        su1, su2, _, _ = _get_coxa_socket_points(geo, leg_idx)
        s_mu = points_from_geo(geo, basecoxamembranemiddle(leg_idx, 2))[0]
        start_u1, start_u2 = points_from_geo(
            geo,
            legsegmentedge(leg_idx, 1, 1, 4),
            legsegmentedge(leg_idx, 1, 1, 3),
        )
        buffer_ratio = _calculate_buffer_ratio(node, geo, leg_idx)
        mid_u, u_inner, b_start_u2, b_start_u1 = fill_pentagon_with_buffer(
            [su1, s_mu, su2, start_u2, start_u1],
            (start_u2, start_u1),
            buffer_ratio,
            (su1, start_u1),
        )
        set_point_id(b_start_u1, legsegmentinset(leg_idx, 1, 1, 4))
        set_point_id(b_start_u2, legsegmentinset(leg_idx, 1, 1, 3))
        set_point_id(mid_u, legsegmentbuffer(leg_idx, 1, 1))
        set_point_id(u_inner, legsegmentbuffer(leg_idx, 1, 2))


def fill_coxa_bottom_pentagon(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    for i in range(4):
        leg_idx = i + 1
        _, _, sb1, sb2 = _get_coxa_socket_points(geo, leg_idx)
        s_mb = points_from_geo(geo, basecoxamembranemiddle(leg_idx, 1))[0]
        start_b1, start_b2 = points_from_geo(
            geo,
            legsegmentedge(leg_idx, 1, 1, 1),
            legsegmentedge(leg_idx, 1, 1, 2),
        )
        buffer_ratio = _calculate_buffer_ratio(node, geo, leg_idx)
        mid_b, b_inner, b_start_b1, b_start_b2 = fill_pentagon_with_buffer(
            [sb2, s_mb, sb1, start_b1, start_b2],
            (start_b1, start_b2),
            buffer_ratio,
            (sb1, start_b1),
        )
        set_point_id(b_start_b1, legsegmentinset(leg_idx, 1, 1, 1))
        set_point_id(b_start_b2, legsegmentinset(leg_idx, 1, 1, 2))
        set_point_id(mid_b, legsegmentbuffer(leg_idx, 1, 3))
        set_point_id(b_inner, legsegmentbuffer(leg_idx, 1, 4))


def fill_coxa_back_faces(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    for i in range(4):
        leg_idx = i + 1
        sb2, su2 = points_from_geo(
            geo,
            basecoxamemebrane(leg_idx, 2),
            basecoxamemebrane(leg_idx, 3),
        )
        b_start_b2, b_start_u2 = points_from_geo(
            geo,
            legsegmentinset(leg_idx, 1, 1, 2),
            legsegmentinset(leg_idx, 1, 1, 3),
        )
        start_b2, start_u2 = points_from_geo(
            geo,
            legsegmentedge(leg_idx, 1, 1, 2),
            legsegmentedge(leg_idx, 1, 1, 3),
        )
        fill_face([sb2, su2, b_start_u2, b_start_b2])
        fill_face([b_start_b2, b_start_u2, start_u2, start_b2])


def fill_coxa_front_faces(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()
    for i in range(4):
        leg_idx = i + 1
        su1, sb1 = points_from_geo(
            geo,
            basecoxamemebrane(leg_idx, 4),
            basecoxamemebrane(leg_idx, 1),
        )
        mid_u, mid_b = points_from_geo(
            geo,
            legsegmentbuffer(leg_idx, 1, 1),
            legsegmentbuffer(leg_idx, 1, 3),
        )
        b_start_u1, b_start_b1 = points_from_geo(
            geo,
            legsegmentinset(leg_idx, 1, 1, 4),
            legsegmentinset(leg_idx, 1, 1, 1),
        )
        start_u1, start_b1 = points_from_geo(
            geo,
            legsegmentedge(leg_idx, 1, 1, 4),
            legsegmentedge(leg_idx, 1, 1, 1),
        )
        fill_face([su1, sb1, mid_b, mid_u])
        fill_face([mid_u, mid_b, b_start_b1, b_start_u1])
        fill_face([b_start_u1, b_start_b1, start_b1, start_u1])


def _adjust_single_coxa_start(
    geo: hou.Geometry,
    leg_idx: int,
    wedge_angle: float,
) -> None:
    pos_sbm = points_from_geo(geo, basecoxamembranemiddle(leg_idx, 1))[0].position()
    su1, su2, _, _ = _get_coxa_socket_points(geo, leg_idx)
    pos_stm = (su1.position() + su2.position()) * 0.5
    direction = hou.Vector3(pos_stm.x() - pos_sbm.x(), 0.0, pos_stm.z() - pos_sbm.z()).normalized()

    coxa_points = _get_coxa_tube_points(geo, leg_idx)
    coxa_start_pts = coxa_points[:4]
    coxa_end_pts = coxa_points[-4:]
    intermediate_ratios = compute_intermediate_ratios(coxa_points)

    pos_b1 = coxa_start_pts[0].position()
    pos_b2 = coxa_start_pts[1].position()
    mid_b = (pos_b1 + pos_b2) * 0.5

    pos_end_b1 = coxa_end_pts[0].position()
    pos_end_b2 = coxa_end_pts[1].position()
    end_mid_b = (pos_end_b1 + pos_end_b2) * 0.5

    y_delta = abs(pos_sbm.y() - mid_b.y())
    wedge_offset = y_delta * math.tan(math.radians(wedge_angle))
    target_mid_b = hou.Vector3(pos_sbm.x(), mid_b.y(), pos_sbm.z()) + direction * wedge_offset

    total_len_b = (end_mid_b - pos_sbm).dot(direction)
    ratio = wedge_offset / total_len_b if total_len_b > 1e-6 else 0.5

    pos_u1 = coxa_start_pts[3].position()
    pos_u2 = coxa_start_pts[2].position()
    mid_u = (pos_u1 + pos_u2) * 0.5

    pos_end_u1 = coxa_end_pts[3].position()
    pos_end_u2 = coxa_end_pts[2].position()
    end_mid_u = (pos_end_u1 + pos_end_u2) * 0.5
    target_mid_u = pos_stm + (end_mid_u - pos_stm) * ratio

    delta_b = target_mid_b - mid_b
    delta_u = target_mid_u - mid_u

    coxa_start_pts[0].setPosition(pos_b1 + delta_b)
    coxa_start_pts[1].setPosition(pos_b2 + delta_b)
    coxa_start_pts[2].setPosition(pos_u2 + delta_u)
    coxa_start_pts[3].setPosition(pos_u1 + delta_u)

    update_intermediate_positions(coxa_points, intermediate_ratios)


def _calculate_buffer_ratio(
    node: hou.SopNode,
    geo: hou.Geometry,
    leg_idx: int,
) -> float:
    control_params = get_parms(get_control(get_parent(node), "CONTROL"), use_tuple=False)
    socket_pts = list(_get_coxa_socket_points(geo, leg_idx))
    coxa_start_pts = list(points_from_geo(geo, *(legsegmentedge(leg_idx, 1, 1, c) for c in (1, 2, 3, 4))))
    return _get_coxa_buffer_ratio(
        socket_pts,
        coxa_start_pts,
        control_params.joint_support_loop_ratio,
    )


def _get_coxa_socket_points(
    geo: hou.Geometry,
    leg_idx: int,
) -> tuple[hou.Point, hou.Point, hou.Point, hou.Point]:
    return points_from_geo(
        geo,
        basecoxamemebrane(leg_idx, 4),
        basecoxamemebrane(leg_idx, 3),
        basecoxamemebrane(leg_idx, 1),
        basecoxamemebrane(leg_idx, 2),
    )


def _get_coxa_tube_points(
    geo: hou.Geometry,
    leg_idx: int,
) -> list[hou.Point]:
    points = unique_points_by_attrib(geo, "id")
    pts = [points[legsegmentedge(leg_idx, 1, 1, c)] for c in (1, 2, 3, 4)]
    pts.extend(points[legsegmentsupport(leg_idx, 1, 1, c)] for c in (1, 2, 3, 4))
    mid_i = 1
    while legsegmentmid(leg_idx, 1, mid_i, 1) in points:
        pts.extend(points[legsegmentmid(leg_idx, 1, mid_i, c)] for c in (1, 2, 3, 4))
        mid_i += 1
    pts.extend(points[legsegmentsupport(leg_idx, 1, -1, c)] for c in (1, 2, 3, 4))
    pts.extend(points[legsegmentedge(leg_idx, 1, -1, c)] for c in (1, 2, 3, 4))
    return pts


def _get_coxa_buffer_ratio(
    socket_points: list[hou.Point] | tuple[hou.Point, ...],
    coxa_start_points: list[hou.Point] | tuple[hou.Point, ...],
    support_loop_ratio: float,
) -> float:
    pos_su1, pos_su2, _, _ = points_to_positions(socket_points)
    _, _, pos_au2, pos_au1 = points_to_positions(coxa_start_points)
    coxa_width = coxa_start_points[0].position().distanceTo(coxa_start_points[1].position())
    cut_length = coxa_width * support_loop_ratio
    pos_su_mid = (pos_su1 + pos_su2) * 0.5
    pos_au_mid = (pos_au1 + pos_au2) * 0.5
    dist_socket_to_start = pos_su_mid.distanceTo(pos_au_mid)
    return 1.0 - cut_length / dist_socket_to_start
