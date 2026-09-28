import math

import hou
from houkit.attributer import add_global_attrib, add_prim_attrib
from houkit.geomath import rotation_to
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topology import fill_face, fill_pentagon_with_buffer, points_to_positions

from ..attributes import GlobalAttrib
from ..bases.attributes import basecoxamemebrane, basecoxamembranemiddle
from ..helper import points_from_geo, set_point_id
from ..segments.attributes import LegParam, legmembrane, legsegment
from ..segments.build import build_leg


def record_global_info(
    node: hou.SopNode,
) -> None:
    parent = get_parent(node)
    geo = node.geometry()

    params = get_parms(parent)
    joint_limits = {
        "min_flex_angles": tuple(params.min_flex_angles),
        "max_flex_angles": tuple(params.max_flex_angles),
        "min_yaw_angles": tuple(params.min_yaw_angles),
        "max_yaw_angles": tuple(params.max_yaw_angles),
    }
    limits_attrib = add_global_attrib(
        geo,
        GlobalAttrib.JOINT_LIMITS,
        joint_limits,
    )
    geo.setGlobalAttribValue(limits_attrib, joint_limits)


def extrude_legs(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()

    for i in range(4):
        leg_idx = i + 1
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

        # sz: small Z, bz: big Z
        pos_top_sz, pos_top_bz, pos_btm_sz, pos_btm_bz = points_to_positions(pts)

        top_mid = (pos_top_sz + pos_top_bz) / 2.0
        btm_mid = (pos_btm_sz + pos_btm_bz) / 2.0
        direction = hou.Vector3(top_mid.x() - btm_mid.x(), 0.0, top_mid.z() - btm_mid.z()).normalized()
        bottom_z_offset = (btm_mid - top_mid).dot(direction)
        origin = top_mid + direction * bottom_z_offset

        param = _get_leg_param(node, i)
        (seg_pts, thickness_pts, mem_pts), warnings = build_leg(geo, param)
        for w in warnings:
            node.addWarning(w)

        q = rotation_to(hou.Vector3(0.0, 0.0, -1.0), direction)
        for pt in seg_pts + thickness_pts + mem_pts:
            pt.setPosition(q.rotate(pt.position()) + origin)

        buffer_loop, pentagon_pts = _adjust_coxa(node, pts, mid_pts, seg_pts[:16])
        _attribute_leg_points(leg_idx, seg_pts, thickness_pts, mem_pts, buffer_loop, pentagon_pts)
        geo.deletePoints(seg_pts[:4])


def _get_leg_param(
    node: hou.SopNode,
    leg_index: int,
) -> LegParam:
    geo = node.geometry()
    parent = get_parent(node)
    params = get_parms(parent, use_tuple=False)
    control_params = get_parms(get_control(parent, "CONTROL"), use_tuple=False)

    front_socket_width = get_front_coxa_socket_width(geo)
    front_coxa_width = front_socket_width * params.front_coxa_width_length_ratios.x()
    front_coxa_length = front_socket_width * params.front_coxa_width_length_ratios.y()

    if leg_index == 0:
        coxa_width = front_coxa_width
        coxa_length = front_coxa_length
    else:
        coxa_width = front_coxa_width * params.other_leg_width_ratios[leg_index - 1]
        coxa_length = front_coxa_length * params.other_leg_length_ratios[leg_index - 1]

    coxa_width_length = (coxa_width, coxa_length)

    return LegParam.from_specs(
        coxa_width_length=coxa_width_length,
        length_ratios=tuple(params.front_segment_length_ratios),
        max_segment_yaws=tuple(params.max_yaw_angles)[1:],
        min_segment_flexes=tuple(params.min_flex_angles)[1:],
        coxa_trochanter_height_ratio=control_params.coxa_trochanter_height_ratio,
        other_segment_height_ratio=control_params.other_segment_height_ratio,
        spine_ratio=control_params.segment_bulge_bias_ratio,
        shrink_ratios=control_params.segment_taper_ratios,
        minimum_membrane=control_params.joint_clearance_limits,
        support_loop_ratio=control_params.joint_support_loop_ratio,
        tarsus_wedge_angle=control_params.tarsus_wedge_angle,
    )


def _adjust_coxa(
    node: hou.SopNode,
    socket_points: list[hou.Point],
    socket_midpoints: list[hou.Point],
    coxa_points: list[hou.Point],
) -> tuple[list[hou.Point], list[hou.Point]]:
    assert len(coxa_points) == 16, f"Expected 16 coxa points, got {len(coxa_points)}"
    assert len(socket_points) == 4, f"Expected 4 socket points, got {len(socket_points)}"
    assert len(socket_midpoints) == 2, f"Expected 2 socket midpoints, got {len(socket_midpoints)}"

    geo = node.geometry()
    add_prim_attrib(geo, "region", "")

    coxa_start_pts = coxa_points[:4]
    coxa_start_support_pts = coxa_points[4:8]
    coxa_end_pts = coxa_points[12:16]

    control_params = get_parms(get_control(get_parent(node), "CONTROL"), use_tuple=False)
    coxa_start_wedge_angle = control_params.coxa_start_wedge_angle
    adjusted_support_positions = _get_adjusted_coxa_support_positions(
        socket_points,
        coxa_end_pts,
        coxa_start_wedge_angle,
    )
    for point, position in zip(coxa_start_support_pts, adjusted_support_positions):
        point.setPosition(position)

    support_loop_ratio = control_params.joint_support_loop_ratio
    buffer_ratio = _get_coxa_buffer_ratio(
        socket_points,
        coxa_start_pts,
        coxa_start_support_pts,
        support_loop_ratio,
    )
    return _build_coxa_socket_faces(
        socket_points,
        socket_midpoints,
        coxa_start_support_pts,
        buffer_ratio,
    )


def _attribute_leg_points(
    leg_idx: int,
    seg_pts: list[hou.Point],
    thickness_pts: list[hou.Point],
    mem_pts: list[hou.Point],
    buffer_loop: list[hou.Point],
    pentagon_pts: list[hou.Point],
) -> None:
    """Assign ID attributes to all segment, thickness, and membrane points of a leg."""
    # 1. Attribute segment points (7 segments)
    # Coxa (seg 1): loop 3 (start wedge), loop 4 (end support), loop 5 (end)
    for loop_offset, loop_idx in enumerate([3, 4, 5], start=1):
        loop_pts = seg_pts[loop_offset * 4 : (loop_offset + 1) * 4]
        for corner_offset, pt in enumerate(loop_pts):
            corner_idx = corner_offset + 1
            set_point_id(pt, legsegment(leg_idx, 1, loop_idx, corner_idx))

    # Coxa start support buffer loop: loop index 2 [lb, rb, ru, lu]
    for corner_offset, pt in enumerate(buffer_loop):
        corner_idx = corner_offset + 1
        set_point_id(pt, legsegment(leg_idx, 1, 2, corner_idx))

    # Coxa socket pentagon & float points
    for k, pt in enumerate(pentagon_pts):
        set_point_id(pt, legsegment(leg_idx, 1, "buffer", k + 1))

    # Other segments (seg 2..7): loops 2, 3, 4, 5
    for seg_i in range(1, 7):
        seg_idx = seg_i + 1
        base = seg_i * 16
        for loop_offset, loop_idx in enumerate([2, 3, 4, 5]):
            loop_pts = seg_pts[base + loop_offset * 4 : base + (loop_offset + 1) * 4]
            for corner_offset, pt in enumerate(loop_pts):
                corner_idx = corner_offset + 1
                set_point_id(pt, legsegment(leg_idx, seg_idx, loop_idx, corner_idx))

    # 2. Attribute thickness points (6 joints, 2 loops each of 4 points:
    #    former segment end inset (loop 6) and latter segment start inset (loop 1))
    for joint_i in range(6):
        former_seg = joint_i + 1
        latter_seg = joint_i + 2
        base = joint_i * 8
        former_inset = thickness_pts[base : base + 4]
        latter_inset = thickness_pts[base + 4 : base + 8]
        for corner_offset, pt in enumerate(former_inset):
            corner_idx = corner_offset + 1
            set_point_id(pt, legsegment(leg_idx, former_seg, 6, corner_idx))
        for corner_offset, pt in enumerate(latter_inset):
            corner_idx = corner_offset + 1
            set_point_id(pt, legsegment(leg_idx, latter_seg, 1, corner_idx))

    # 3. Attribute membrane points (6 joints, 3 loops each of 4 points:
    #    loop 1: former support, loop 2: middle, loop 3: latter support)
    for joint_i in range(6):
        joint_idx = joint_i + 1
        base = joint_i * 12
        for loop_offset, loop_idx in enumerate([1, 2, 3]):
            loop_pts = mem_pts[base + loop_offset * 4 : base + (loop_offset + 1) * 4]
            for corner_offset, pt in enumerate(loop_pts):
                corner_idx = corner_offset + 1
                set_point_id(pt, legmembrane(leg_idx, joint_idx, loop_idx, corner_idx))


def _get_adjusted_coxa_support_positions(
    socket_points: list[hou.Point],
    coxa_end_points: list[hou.Point],
    coxa_start_wedge_angle: float,
) -> tuple[hou.Vector3, hou.Vector3, hou.Vector3, hou.Vector3]:
    # su: socket upper, sb: socket bottom
    pos_su1, pos_su2, pos_sb1, pos_sb2 = points_to_positions(socket_points)
    # pos_bb: base bottom (lb, rb), pos_bu: base upper (ru, lu)
    pos_bb1, pos_bb2, pos_bu2, pos_bu1 = points_to_positions(coxa_end_points)

    pos_ab1 = _get_adjusted_bottom_coxa_position(pos_sb1, pos_bb1, coxa_start_wedge_angle)
    pos_ab2 = _get_adjusted_bottom_coxa_position(pos_sb2, pos_bb2, coxa_start_wedge_angle)
    pos_au1 = (pos_su1 + pos_bu1) * 0.5
    pos_au2 = (pos_su2 + pos_bu2) * 0.5
    # Return ordered [lb, rb, ru, lu]
    return pos_ab1, pos_ab2, pos_au2, pos_au1


def _get_adjusted_bottom_coxa_position(
    socket_position: hou.Vector3,
    base_position: hou.Vector3,
    wedge_angle: float,
) -> hou.Vector3:
    y_delta = abs(socket_position.y() - base_position.y())
    xz_delta = math.sqrt(
        (base_position.x() - socket_position.x()) ** 2
        + (base_position.z() - socket_position.z()) ** 2
    )
    ratio = (
        y_delta * math.tan(math.radians(wedge_angle)) / xz_delta
        if xz_delta > 1e-6 else
        0.5
    )
    return hou.Vector3(
        socket_position.x() + (base_position.x() - socket_position.x()) * ratio,
        base_position.y(),
        socket_position.z() + (base_position.z() - socket_position.z()) * ratio,
    )


def _get_coxa_buffer_ratio(
    socket_points: list[hou.Point],
    coxa_start_points: list[hou.Point],
    support_points: list[hou.Point],
    support_loop_ratio: float,
) -> float:
    pos_su1, pos_su2, _, _ = points_to_positions(socket_points)
    _, _, pos_au2, pos_au1 = points_to_positions(support_points)
    coxa_width = coxa_start_points[0].position().distanceTo(coxa_start_points[1].position())
    cut_length = coxa_width * support_loop_ratio
    pos_su_mid = (pos_su1 + pos_su2) * 0.5
    pos_au_mid = (pos_au1 + pos_au2) * 0.5
    dist_socket_to_support = pos_su_mid.distanceTo(pos_au_mid)
    return 1.0 - cut_length / dist_socket_to_support


def _build_coxa_socket_faces(
    socket_points: list[hou.Point],
    socket_midpoints: list[hou.Point],
    support_points: list[hou.Point],
    buffer_ratio: float,
) -> tuple[list[hou.Point], list[hou.Point]]:
    # su: socket upper, sb: socket bottom
    su1, su2, sb1, sb2 = socket_points
    # s_mu, s_mb: socket midpoint upper / bottom
    s_mu, s_mb = socket_midpoints
    # eb: support bottom (lb, rb), eu: support upper (ru, lu)
    eb1, eb2, eu2, eu1 = support_points

    # Upper pentagon: su1, s_mu, su2, eu2, eu1
    mid_u, u_inner, b_eu2, b_eu1 = fill_pentagon_with_buffer(
        [su1, s_mu, su2, eu2, eu1],
        (eu2, eu1),
        buffer_ratio,
        (su1, eu1),
    )
    # Bottom pentagon: sb2, s_mb, sb1, eb1, eb2
    mid_b, b_inner, b_eb1, b_eb2 = fill_pentagon_with_buffer(
        [sb2, s_mb, sb1, eb1, eb2],
        (eb1, eb2),
        buffer_ratio,
        (sb1, eb1),
    )

    # Back side (+Z): split into 2 quads by (b_eu2, b_eb2)
    fill_face([sb2, su2, b_eu2, b_eb2])
    fill_face([b_eb2, b_eu2, eu2, eb2])

    # Front side (-Z): split into 3 quads by (mid_u, mid_b) and (b_eu1, b_eu1)
    fill_face([su1, sb1, mid_b, mid_u])
    fill_face([mid_u, mid_b, b_eb1, b_eu1])
    fill_face([b_eu1, b_eb1, eb1, eu1])

    buffer_loop = [b_eb1, b_eb2, b_eu2, b_eu1]
    pentagon_pts = [mid_u, u_inner, mid_b, b_inner]
    return buffer_loop, pentagon_pts


def get_front_coxa_socket_width(geo: hou.Geometry) -> float:
    pos_top_sz, pos_top_bz = points_from_geo(
        geo,
        basecoxamemebrane(1, 4),
        basecoxamemebrane(1, 3),
    )
    return (pos_top_bz.position() - pos_top_sz.position()).length()
