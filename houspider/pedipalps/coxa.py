import hou

from houkit.geomath import is_zero_approx, line_intersect_face, line_intersect_line
from houkit.noder import get_control, get_parent
from houkit.parameterizer import get_float_parm, get_parms
from houkit.topology import fill_face

from ..bases.attributes import basemaxillamembrane
from ..cheliceraes.attributes import cheliceraestartmembranesupport
from ..helper import add_id_point, points_from_geo, positions_from_geo
from .attributes import pedipalpcoxabuffer, pedipalpsegment
from .geometry import get_buffer_dist_z, get_coxa_base_direction


def fill_bottom_right_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    es4, c2, m1, cb = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 4, 2),
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
        pedipalpsegment(1, 1, 4, 3),
        pedipalpsegment(1, 1, 4, 2),
        basemaxillamembrane(1),
    )
    fill_face([es3, es4, m1, s3])


def fill_top_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()

    e2, m2, m3, m4, es2, es3 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 4),
        basemaxillamembrane(2),
        basemaxillamembrane(3),
        basemaxillamembrane(4),
        pedipalpsegment(1, 1, 4, 4),
        pedipalpsegment(1, 1, 4, 3),
    )

    direction = get_coxa_base_direction(geo)
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


def add_maxilla_quads(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    pos = _get_maxilla_pole(node)
    normal = _get_averaged_maxilla_quad_normal(geo, pos)
    _add_maxilla_quads_to_geo(geo, pos, normal, control_params.endite_surface_size_ratio)

def _get_maxilla_pole(node: hou.SopNode) -> hou.Vector3:
    geo: hou.Geometry = node.geometry()
    pedipalp = get_parent(node)
    length_ratio = get_float_parm(pedipalp, "endite_length_ratio")

    e1, e2, e3, m1, m2, m4, ct2 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 1),
        pedipalpsegment(1, 1, 5, 4),
        pedipalpsegment(1, 1, 5, 3),
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


def add_front_upper_face(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    p = _add_front_face_point(geo, control_params.endite_buffer_ratios)
    es2, c6, m2 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 4, 4),
        pedipalpcoxabuffer(1, "fronttop"),
        basemaxillamembrane(2),
    )
    fill_face([es2, c6, m2, p])

def _add_front_face_point(
    geo: hou.Geometry,
    endite_buffer: hou.Vector2,
) -> hou.Point:
    e1, e2 = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 1),
        pedipalpsegment(1, 1, 5, 4),
    )
    dist = get_buffer_dist_z(geo, endite_buffer.y())
    direction = get_coxa_base_direction(geo)
    start = e1.position() * endite_buffer.x() + e2.position() * (1.0 - endite_buffer.x())
    target = start + direction * dist
    return add_id_point(geo, target, pedipalpcoxabuffer(1, "front"))


def add_front_loop_faces(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    control_params = get_parms(get_control(node, "CONTROL"), use_tuple=False)
    p = _add_loop_point(geo, control_params.endite_buffer_ratios.y())
    es1, es2, es4, cf, cb = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 4, 1),
        pedipalpsegment(1, 1, 4, 4),
        pedipalpsegment(1, 1, 4, 2),
        pedipalpcoxabuffer(1, "front"),
        pedipalpcoxabuffer(1, "bottom"),
    )
    fill_face([es2, cf, p, es1])
    fill_face([es1, p, cb, es4])

def _add_loop_point(
    geo: hou.Geometry,
    endite_buffer_y: float,
) -> hou.Point:
    e1, = points_from_geo(
        geo,
        pedipalpsegment(1, 1, 5, 1),
    )
    dist = get_buffer_dist_z(geo, endite_buffer_y)
    direction = get_coxa_base_direction(geo)
    target = e1.position() + direction * dist
    return add_id_point(geo, target, pedipalpcoxabuffer(1, "frontbottom"))


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
