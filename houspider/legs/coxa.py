import math

import hou
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topology import fill_face, fill_pentagon_with_buffer, points_to_positions

from ..helper import set_point_id
from ..segments.helper import compute_intermediate_ratios, update_intermediate_positions
from .attributes import legsegment


def adjust_coxa(
    node: hou.SopNode,
    socket_points: list[hou.Point],
    socket_midpoints: list[hou.Point],
    coxa_points: list[hou.Point],
) -> tuple[list[hou.Point], list[hou.Point]]:
    assert len(coxa_points) >= 8 and len(coxa_points) % 4 == 0, f"Expected coxa_points length to be a multiple of 4 (>= 8), got {len(coxa_points)}"
    assert len(socket_points) == 4, f"Expected 4 socket points, got {len(socket_points)}"
    assert len(socket_midpoints) == 2, f"Expected 2 socket midpoints, got {len(socket_midpoints)}"

    coxa_start_pts = coxa_points[:4]
    coxa_end_pts = coxa_points[-4:]

    intermediate_ratios = compute_intermediate_ratios(coxa_points)

    control_params = get_parms(get_control(get_parent(node), "CONTROL"), use_tuple=False)
    adjusted_start_positions = _get_adjusted_coxa_start_positions(
        socket_points,
        coxa_end_pts,
        control_params.coxa_start_wedge_angle,
    )
    for point, position in zip(coxa_start_pts, adjusted_start_positions):
        point.setPosition(position)

    update_intermediate_positions(coxa_points, intermediate_ratios)

    support_loop_ratio = control_params.joint_support_loop_ratio
    buffer_ratio = _get_coxa_buffer_ratio(
        socket_points,
        coxa_start_pts,
        support_loop_ratio,
    )
    return _build_coxa_socket_faces(
        socket_points,
        socket_midpoints,
        coxa_start_pts,
        buffer_ratio,
    )


def attribute_coxa_buffer(
    leg_idx: int,
    buffer_loop: list[hou.Point],
    pentagon_pts: list[hou.Point],
) -> None:
    for corner_offset, pt in enumerate(buffer_loop):
        corner_idx = corner_offset + 1
        set_point_id(pt, legsegment(leg_idx, 1, 1, corner_idx))

    for k, pt in enumerate(pentagon_pts):
        set_point_id(pt, legsegment(leg_idx, 1, "buffer", k + 1))


def _get_adjusted_coxa_start_positions(
    socket_points: list[hou.Point],
    coxa_end_points: list[hou.Point],
    coxa_start_wedge_angle: float,
) -> tuple[hou.Vector3, hou.Vector3, hou.Vector3, hou.Vector3]:
    # su: socket upper, sb: socket bottom
    pos_su1, pos_su2, pos_sb1, pos_sb2 = points_to_positions(socket_points)
    # pos_bb: base bottom (lb, rb), pos_bu: base upper (ru, lu)
    pos_bb1, pos_bb2, pos_bu2, pos_bu1 = points_to_positions(coxa_end_points)

    pos_ab1, pos_au1 = _adjust_side_positions(pos_su1, pos_sb1, pos_bu1, pos_bb1, coxa_start_wedge_angle)
    pos_ab2, pos_au2 = _adjust_side_positions(pos_su2, pos_sb2, pos_bu2, pos_bb2, coxa_start_wedge_angle)
    # Return ordered [lb, rb, ru, lu]
    return pos_ab1, pos_ab2, pos_au2, pos_au1


def _adjust_side_positions(
    pos_su: hou.Vector3,
    pos_sb: hou.Vector3,
    pos_bu: hou.Vector3,
    pos_bb: hou.Vector3,
    wedge_angle: float,
) -> tuple[hou.Vector3, hou.Vector3]:
    """Calculate adjusted (bottom, upper) positions for one side of coxa start section."""
    y_delta = abs(pos_sb.y() - pos_bb.y())
    xz_dist = math.hypot(pos_bb.x() - pos_sb.x(), pos_bb.z() - pos_sb.z())
    ratio = y_delta * math.tan(math.radians(wedge_angle)) / xz_dist if xz_dist > 1e-6 else 0.5

    pos_ab = hou.Vector3(
        pos_sb.x() + (pos_bb.x() - pos_sb.x()) * ratio,
        pos_bb.y(),
        pos_sb.z() + (pos_bb.z() - pos_sb.z()) * ratio,
    )
    pos_au = hou.Vector3(
        pos_su.x() + (pos_bu.x() - pos_su.x()) * ratio,
        pos_bu.y(),
        pos_su.z() + (pos_bu.z() - pos_su.z()) * ratio,
    )
    return pos_ab, pos_au


def _get_coxa_buffer_ratio(
    socket_points: list[hou.Point],
    coxa_start_points: list[hou.Point],
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


def _build_coxa_socket_faces(
    socket_points: list[hou.Point],
    socket_midpoints: list[hou.Point],
    start_points: list[hou.Point],
    buffer_ratio: float,
) -> tuple[list[hou.Point], list[hou.Point]]:
    # su: socket upper, sb: socket bottom
    su1, su2, sb1, sb2 = socket_points
    # s_mu, s_mb: socket midpoint upper / bottom
    s_mu, s_mb = socket_midpoints
    # start_b: start bottom (lb, rb), start_u: start upper (ru, lu)
    start_b1, start_b2, start_u2, start_u1 = start_points

    # Upper pentagon: su1, s_mu, su2, start_u2, start_u1
    mid_u, u_inner, b_start_u2, b_start_u1 = fill_pentagon_with_buffer(
        [su1, s_mu, su2, start_u2, start_u1],
        (start_u2, start_u1),
        buffer_ratio,
        (su1, start_u1),
    )
    # Bottom pentagon: sb2, s_mb, sb1, start_b1, start_b2
    mid_b, b_inner, b_start_b1, b_start_b2 = fill_pentagon_with_buffer(
        [sb2, s_mb, sb1, start_b1, start_b2],
        (start_b1, start_b2),
        buffer_ratio,
        (sb1, start_b1),
    )

    # Back side (+Z): split into 2 quads by (b_start_u2, b_start_b2)
    fill_face([sb2, su2, b_start_u2, b_start_b2])
    fill_face([b_start_b2, b_start_u2, start_u2, start_b2])

    # Front side (-Z): split into 3 quads by (mid_u, mid_b) and (b_start_u1, b_start_u1)
    fill_face([su1, sb1, mid_b, mid_u])
    fill_face([mid_u, mid_b, b_start_b1, b_start_b1])
    fill_face([b_start_u1, b_start_b1, start_b1, start_u1])

    buffer_loop = [b_start_b1, b_start_b2, b_start_u2, b_start_u1]
    pentagon_pts = [mid_u, u_inner, mid_b, b_inner]
    return buffer_loop, pentagon_pts
