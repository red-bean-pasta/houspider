import hou

from houkit.attributer import points_start_with
from houkit.geomath import is_zero_approx, line_intersect_face
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_float_parm, get_parms
from houkit.topology import fill_face

from .attributes import pedipalpcoxabuffer, pedipalpsegmentedge, pedipalpsegmentsupport
from ..bases.attributes import basemaxillamembrane
from ..cheliceraes.attributes import cheliceraestartmembranesupport
from ..helper import add_id_point, points_from_geo, positions_from_geo


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


def fill_bottom_right_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    es4, c2, m1, cb = points_from_geo(
        geo,
        pedipalpsegmentsupport(1, 1, -1, 2),
        pedipalpcoxabuffer(1, "base", 2),
        basemaxillamembrane(1),
        pedipalpcoxabuffer(1, "bottom"),
    )
    fill_face([es4, cb, c2, m1])


def fill_back_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    s3, es3, es4, m1 = points_from_geo(
        geo,
        pedipalpcoxabuffer(1, "start", 3),
        pedipalpsegmentsupport(1, 1, -1, 3),
        pedipalpsegmentsupport(1, 1, -1, 2),
        basemaxillamembrane(1),
    )
    fill_face([es3, es4, m1, s3])


def fill_top_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()

    e2, m2, m3, m4, es2, es3 = points_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 4),
        basemaxillamembrane(2),
        basemaxillamembrane(3),
        basemaxillamembrane(4),
        pedipalpsegmentsupport(1, 1, -1, 4),
        pedipalpsegmentsupport(1, 1, -1, 3),
    )

    direction = _get_coxa_base_direction(geo)
    assert not is_zero_approx(direction.z())

    base = get_parent(node).input(0)
    target_z = points_from_geo(
        base.geometry(),
        cheliceraestartmembranesupport(4),
    )[0].position().z()
    z_offset = target_z - e2.position().z()
    offset = z_offset / direction.z() * direction
    pos = e2.position() + offset

    cf = add_id_point(geo, pos, pedipalpcoxabuffer(1, "fronttop"))

    fill_face([es3, m4, cf, es2])
    fill_face([m4, m3, m2, cf])


def add_front_upper_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    p = _add_front_face_point(geo, control_params.endite_buffer_ratios)
    es2, c6, m2 = points_from_geo(
        geo,
        pedipalpsegmentsupport(1, 1, -1, 4),
        pedipalpcoxabuffer(1, "fronttop"),
        basemaxillamembrane(2),
    )
    fill_face([es2, c6, m2, p])


def add_front_loop_faces(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    p = _add_loop_point(geo, control_params.endite_buffer_ratios.y())
    es1, es2, es4, cf, cb = points_from_geo(
        geo,
        pedipalpsegmentsupport(1, 1, -1, 1),
        pedipalpsegmentsupport(1, 1, -1, 4),
        pedipalpsegmentsupport(1, 1, -1, 2),
        pedipalpcoxabuffer(1, "front"),
        pedipalpcoxabuffer(1, "bottom"),
    )
    fill_face([es2, cf, p, es1])
    fill_face([es1, p, cb, es4])


def add_maxilla_quads(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    parent = get_parent(node)
    endite_surface_size_ratio = get_float_parm(parent, 'endite_surface_size_ratio')
    pos = _get_maxilla_pole(node)
    normal = _get_averaged_maxilla_quad_normal(geo, pos)
    _add_maxilla_quads_to_geo(geo, pos, normal, endite_surface_size_ratio)


def fill_maxilla_faces(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    cf, cfb, cb, ct2, ct1, m2 = points_from_geo(
        geo,
        pedipalpcoxabuffer(1, "front"),
        pedipalpcoxabuffer(1, "frontbottom"),
        pedipalpcoxabuffer(1, "bottom"),
        pedipalpcoxabuffer(1, "base", 2),
        pedipalpcoxabuffer(1, "base", 1),
        basemaxillamembrane(2),
    )
    p0, p1, p2, p3, p4, p5 = points_from_geo(
        geo,
        *[pedipalpcoxabuffer(1, "maxilla", i + 1) for i in range(6)],
    )
    fill_face([p0, m2, ct1, p4])
    fill_face([p4, ct1, ct2, p3])
    fill_face([p3, ct2, cb, p2])
    fill_face([p2, cb, cfb, p5])
    fill_face([p5, cfb, cf, p1])
    fill_face([p1, cf, m2, p0])


def _add_bottom_right_face_point(
    geo: hou.Geometry,
    endite_buffer: hou.Vector2,
) -> hou.Point:
    e1, e2, m1 = points_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 1),
        pedipalpsegmentedge(1, 1, -1, 2),
        basemaxillamembrane(1),
    )

    direction = _get_coxa_base_direction(geo)

    start_position = e1.position() * endite_buffer.x() + e2.position() * (1.0 - endite_buffer.x())
    dist = _get_buffer_dist_z(geo, endite_buffer.y())
    target_position = start_position + direction * dist
    p = add_id_point(geo, target_position, pedipalpcoxabuffer(1, "bottom"))
    return p


def _add_base_trapezoid(
    node: hou.SopNode,
) -> float:
    geo = node.geometry()
    m1, m2, cb, es4, e1, e4 = points_from_geo(
        geo,
        basemaxillamembrane(1),
        basemaxillamembrane(2),
        pedipalpcoxabuffer(1, "bottom"),
        pedipalpsegmentsupport(1, 1, -1, 2),
        pedipalpsegmentedge(1, 1, -1, 1),
        pedipalpsegmentedge(1, 1, -1, 2),
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
    legs = node.parent().input(1)
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


def _add_front_face_point(
    geo: hou.Geometry,
    endite_buffer: hou.Vector2,
) -> hou.Point:
    e1, e2 = points_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 1),
        pedipalpsegmentedge(1, 1, -1, 4),
    )
    dist = _get_buffer_dist_z(geo, endite_buffer.y())
    direction = _get_coxa_base_direction(geo)
    start = e1.position() * endite_buffer.x() + e2.position() * (1.0 - endite_buffer.x())
    target = start + direction * dist
    return add_id_point(geo, target, pedipalpcoxabuffer(1, "front"))


def _add_loop_point(
    geo: hou.Geometry,
    endite_buffer_y: float,
) -> hou.Point:
    e1, = points_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 1),
    )
    dist = _get_buffer_dist_z(geo, endite_buffer_y)
    direction = _get_coxa_base_direction(geo)
    target = e1.position() + direction * dist
    return add_id_point(geo, target, pedipalpcoxabuffer(1, "frontbottom"))


def _get_maxilla_pole(node: hou.SopNode) -> hou.Vector3:
    geo: hou.Geometry = node.geometry()
    pedipalp = get_parent(node)
    length_ratio = get_float_parm(pedipalp, "endite_length_ratio")

    e1, e2, e3, m1, m2, m4, ct2 = points_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 1),
        pedipalpsegmentedge(1, 1, -1, 4),
        pedipalpsegmentedge(1, 1, -1, 3),
        basemaxillamembrane(1),
        basemaxillamembrane(2),
        basemaxillamembrane(4),
        pedipalpcoxabuffer(1, "base", 2),
    )
    direction = m4.position() - m1.position()
    direction = hou.Vector3(direction.x(), 0, direction.z())

    m2_pos = m2.position()
    hit = line_intersect_face(
        (m2_pos, m2_pos + direction * 100),
        (e1.position(), e2.position(), e3.position()),
    )
    assert hit is not None
    start_pos = m2_pos + (hit - m2_pos) * length_ratio

    v1 = ct2.position() - start_pos
    v2 = (e1.position() - e2.position()).normalized()
    end_pos = start_pos + v2 * v1.dot(v2)
    return end_pos


def _get_averaged_maxilla_quad_normal(geo: hou.Geometry, target: hou.Vector3) -> hou.Vector3:
    pts = points_from_geo(
        geo,
        pedipalpcoxabuffer(1, "front"),
        basemaxillamembrane(2),
        pedipalpcoxabuffer(1, "base", 2),
        pedipalpcoxabuffer(1, "base", 1),
        pedipalpcoxabuffer(1, "bottom"),
        pedipalpcoxabuffer(1, "frontbottom"),
    )

    total = hou.Vector3()
    for p in pts:
        v = (target - p.position()).normalized()
        total += v
    return total.normalized()


def _add_maxilla_quads_to_geo(
    geo: hou.Geometry,
    center: hou.Vector3,
    normal: hou.Vector3,
    flat_ratio: float,
) -> list[hou.Point]:
    ct2p, cbp, cfp, m2p = positions_from_geo(
        geo,
        pedipalpcoxabuffer(1, "base", 2),
        pedipalpcoxabuffer(1, "bottom"),
        pedipalpcoxabuffer(1, "front"),
        basemaxillamembrane(2),
    )

    w = ct2p.distanceTo(center) * flat_ratio
    h = w * (cbp.distanceTo(cfp)) / (cbp.distanceTo(ct2p))
    hw = w * 0.5
    hh = h * 0.5

    u = (cbp - m2p).normalized()
    u = hou.Vector3(u.x(), 0, u.z()).normalized()
    v = normal.cross(u).normalized()

    pw = u * hw
    ph = v * hh
    p0 = center + (-pw - ph)
    p1 = center + (pw - ph)
    p2 = center + (pw + ph)
    p3 = center + (-pw + ph)
    p4 = (p0 + p3) * 0.5
    p5 = (p1 + p2) * 0.5

    poses = [p0, p1, p2, p3, p4, p5]
    pts = []
    for i, p in enumerate(poses, start=1):
        p = add_id_point(geo, p, pedipalpcoxabuffer(1, "maxilla", i))
        pts.append(p)

    fill_face([pts[0], pts[1], pts[5], pts[4]], True)
    fill_face([pts[5], pts[4], pts[3], pts[2]])

    return pts


def _get_coxa_base_direction(geo: hou.Geometry) -> hou.Vector3:
    es3, e3 = points_from_geo(
        geo,
        pedipalpsegmentsupport(1, 1, -1, 3),
        pedipalpsegmentedge(1, 1, -1, 3),
    )
    return (es3.position() - e3.position()).normalized()


def _get_buffer_dist_z(geo: hou.Geometry, endite_buffer_y: float) -> float:
    e1, m1 = positions_from_geo(
        geo,
        pedipalpsegmentedge(1, 1, -1, 1),
        basemaxillamembrane(1),
    )
    return e1.distanceTo(m1) * endite_buffer_y
