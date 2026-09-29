import hou
from houkit.attributer import points_start_with
from houkit.geomath import rotation_to
from houkit.models import Moject
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_parms
from houkit.topologies.basic import remove_unused_points
from houkit.topology import fill_face

from ..bases.attributes import basecoxamemebrane, basemaxillamembrane
from ..helper import add_id_point, points_from_geo, positions_from_geo, prims_by_attr, set_point_id
from ..segments.models import LimbAttributes, LimbParam
from ..segments.build import build_segment_bases
from .attributes import Region, pedipalpcoxabuffer, pedipalpmembrane, pedipalpsegment


def remove_noise_points(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()

    pts = points_start_with(geo, "id", basemaxillamembrane())
    geo.deletePoints(list(p for p in geo.points() if p not in pts))


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


def delete_start_coxa_supports(
    node: hou.SopNode,
) -> None:
    geo: hou.Geometry = node.geometry()
    pts = points_start_with(geo, "id", pedipalpcoxabuffer(1, "support"))
    geo.deletePoints(list(pts))

    starts = points_from_geo(
        geo,
        pedipalpcoxabuffer(1, "start", 1),
        pedipalpcoxabuffer(1, "start", 2),
        pedipalpcoxabuffer(1, "start", 4),
    )
    geo.deletePoints(list(starts))


def prepare_coxa_base_trapezoid(
    node: hou.SopNode,
) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    _add_bottom_right_face_point(geo, control_params.endite_buffer_ratios)
    _add_base_trapezoid(node)

def _add_bottom_right_face_point(
    geo: hou.Geometry,
    endite_buffer: hou.Vector2,
) -> hou.Point:
    e1, e2, m1 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 1),
        pedipalpsegment(1, 1, 5, 2),
        basemaxillamembrane(1),
    )

    direction = get_coxa_base_direction(geo)

    start_position = e1.position() * endite_buffer.x() + e2.position() * (1.0 - endite_buffer.x())
    dist = get_buffer_dist_z(geo, endite_buffer.y())
    target_position = start_position + direction * dist
    p = add_id_point(geo, target_position, pedipalpcoxabuffer(1, "bottom"))
    return p


def cleanup(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()

    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.PEDIPALPSEGMENT)

    remove_unused_points(geo)


def _build_segments(
    node: hou.SopNode,
) -> Moject[tuple[list[hou.Point], list[hou.Point], list[hou.Point]]]:
    geo = node.geometry()
    param = _get_pedipalp_param(node)
    attributes = _get_pedipalp_attributes()
    result = build_segment_bases(geo, param, attributes)
    (all_seg_pts, thickness_pts, all_mem_pts), _ = result

    _attribute_pedipalp_coxa_buffers(1, all_seg_pts[:8])

    return result


def _get_pedipalp_attributes(side: int = 1) -> LimbAttributes:
    return LimbAttributes(
        segment_region=Region.PEDIPALPSEGMENT,
        membrane_region=Region.PEDIPALPMEMBRANE,
        segment_id=lambda a: pedipalpsegment(side, *a),
        membrane_id=lambda a: pedipalpmembrane(side, *a),
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
    front_coxa_length = (
        _get_front_coxa_socket_width(base.geometry())
        * leg_params.coxa_width_length_ratios.y()
    )

    coxa_width_length = _get_pedipalp_coxa_width_length(
        geo,
        front_coxa_length,
        params.pedipalp_coxa_length,
    )
    length_ratios = tuple(params.pedipalp_segment_length_ratios)
    max_segment_yaws = tuple(leg_params.max_yaw_angles)[1:len(length_ratios) + 1]
    min_segment_flexes = tuple(leg_params.min_flex_angles)[1:len(length_ratios) + 1]

    return LimbParam.from_specs(
        coxa_width_length=coxa_width_length,
        length_ratios=length_ratios,
        max_segment_yaws=max_segment_yaws,
        min_segment_flexes=min_segment_flexes,
        coxa_trochanter_height_ratio=control_params.coxa_trochanter_height_ratio,
        other_segment_height_ratio=control_params.other_segment_height_ratio,
        spine_ratio=control_params.segment_bulge_bias_ratio,
        shrink_ratios=control_params.segment_taper_ratios,
        minimum_membrane=control_params.joint_clearance_limits,
        support_loop_ratio=control_params.joint_support_loop_ratio,
        tarsus_wedge_angle=control_params.tarsus_wedge_angle,
    )

def _get_pedipalp_coxa_width_length(
    geo: hou.Geometry,
    front_coxa_length: float,
    pedipalp_coxa_length: float,
) -> tuple[float, float]:
    m3, m4 = positions_from_geo(geo, basemaxillamembrane(3), basemaxillamembrane(4))
    width = m3.distanceTo(m4)
    length = front_coxa_length * pedipalp_coxa_length
    return width, length

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
        return list(geo.points())
    return list(pts)


def _get_legs_node(node: hou.SopNode) -> hou.SopNode:
    legs = get_parent(node).input(1)
    assert legs is not None, "Expected legs as pedipalps input 1"
    return legs


def _get_front_coxa_socket_width(geo: hou.Geometry) -> float:
    pos_top_sz, pos_top_bz = points_from_geo(
        geo,
        basecoxamemebrane(1, 4),
        basecoxamemebrane(1, 3),
    )
    return (pos_top_bz.position() - pos_top_sz.position()).length()



def _add_base_trapezoid(
    node: hou.SopNode,
) -> float:
    geo = node.geometry()
    m1, m2, cb, es4, e1, e4 = points_from_geo(
        geo,
        basemaxillamembrane(1),
        basemaxillamembrane(2),
        pedipalpcoxabuffer(1, "bottom"),
        pedipalpsegment(1, 1, 4, 2),
        pedipalpsegment(1, 1, 5, 1),
        pedipalpsegment(1, 1, 5, 2),
    )

    pos_mid_bottom = (e1.position() + e4.position()) * 0.5

    pos_p4, pos_p3, height = _calculate_base_trapezoid_points(
        node,
        m1.position(),
        m2.position(),
        cb.position(),
        es4.position(),
        pos_mid_bottom,
    )

    p3 = add_id_point(geo, pos_p3, pedipalpcoxabuffer(1, "base", 1))
    p4 = add_id_point(geo, pos_p4, pedipalpcoxabuffer(1, "base", 2))

    fill_face([m1, m2, p3, p4], reverse_order=True)

    return height

def _calculate_base_trapezoid_points(
    node: hou.SopNode,
    pos_m1: hou.Vector3,
    pos_m2: hou.Vector3,
    pos_cb: hou.Vector3,
    pos_es4: hou.Vector3,
    pos_mid_bottom: hou.Vector3,
) -> tuple[hou.Vector3, hou.Vector3, float]:
    geo = node.geometry()
    legs = _get_legs_node(node)
    wedge_angle = get_parms(get_control(legs, "CONTROL"), use_tuple=False).coxa_start_wedge_angle

    m4 = points_from_geo(geo, basemaxillamembrane(4))[0]
    neg_z = hou.Vector3(0.0, 0.0, -1.0)
    n_socket = (pos_m2 - pos_m1).cross(m4.position() - pos_m1).normalized()
    if n_socket.dot(neg_z) < 0:
        n_socket = -n_socket

    edge = pos_m2 - pos_m1
    u = edge.normalized()
    length = edge.length()

    n = hou.Quaternion(90.0 - wedge_angle, u).rotate(n_socket)
    v = n.cross(u).normalized()
    if v.y() > 0.0:
        v = -v
    n_plane = u.cross(v).normalized()

    dir_line = pos_m1 - pos_es4
    denom = dir_line.dot(n_plane)
    t = (pos_m1 - pos_cb).dot(n_plane) / denom
    pos_pp1 = pos_cb + dir_line * t

    offset_pp = (pos_pp1 - pos_m1).dot(u)
    pos_pp2 = pos_pp1 + u * (length - 2.0 * offset_pp)
    mid_pp = (pos_pp1 + pos_pp2) * 0.5

    n_bottom_plane = (pos_cb - pos_es4).cross(pos_m1 - pos_es4).normalized()
    d = (pos_mid_bottom - mid_pp).dot(n_bottom_plane)
    offset_vec = n_bottom_plane * d

    pos_p4 = pos_pp1 + offset_vec
    pos_p3 = pos_pp2 + offset_vec

    offset = (pos_p4 - pos_m1).dot(u)
    height = (pos_p4 - pos_m1 - u * offset).length()

    return pos_p4, pos_p3, height


def get_coxa_base_direction(geo: hou.Geometry) -> hou.Vector3:
    es3, e3 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 4, 3),
        pedipalpsegment(1, 1, 5, 3),
    )
    return (es3.position() - e3.position()).normalized()


def get_buffer_dist_z(geo: hou.Geometry, endite_buffer_y: float) -> float:
    e1, m1 = positions_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 1),
        basemaxillamembrane(1),
    )
    return e1.distanceTo(m1) * endite_buffer_y
