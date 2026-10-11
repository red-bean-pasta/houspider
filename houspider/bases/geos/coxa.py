import math
from typing import Iterable

from hou import SopNode, Point, Prim, Geometry, Vector3
from houkit.attributings.querier import unique_points_by_attrib
from houkit.noder import get_parent
from houkit.parameterizer import get_float_parm
from houkit.topology import outset, split_point

from houspider.bases.attributes import ID, Region, basesternum, basesternummiddle
from houspider.helper import get_control_parms, points_from_geo, prims_by_attr
from houkit.geomath import reflect_point_across_edge
from houspider.sternums import attributes as sternum_attributes


def extrude_sternum_rim(node: SopNode) -> None:
    geo = node.geometry()
    parent = get_parent(node)
    original_points = set(geo.points())

    flap_ratio = get_float_parm(parent, "coxa_height_ratio")
    island_prims_map = outset(list(geo.prims()), flap_ratio * 2.0, use_ratio=True, follow_existing_edge=False)
    assert len(island_prims_map) == 1
    prims = list(island_prims_map.values())[0]
    new_points = [p for p in geo.points() if p not in original_points]

    _attrib_new_points(new_points)
    _attrib_new_prims(prims)
    _align_midline_points(geo)
    _split_for_maxilla(geo)
    _split_for_pedicel(geo)


def rotate_middle_edges(node: SopNode) -> None:
    geo = node.geometry()
    for side in (1, -1):
        for index in range(1, 5):
            _rotate_single_middle_edge(geo, side, index)


def rotate_coxa_flaps(node: SopNode) -> None:
    geo = node.geometry()

    params = get_control_parms(node)
    angle = math.radians(params.coxa_rise_angle)
    sin_angle = math.sin(angle)
    cos_angle = math.cos(angle)

    rotated = set()
    for prim in prims_by_attr(geo, "region", Region.COXA):
        points = prim.points()
        for origin, outer in ((points[0], points[1]), (points[3], points[2])):
            if outer.number() in rotated:
                continue
            rotated.add(outer.number())
            offset = outer.position() - origin.position()
            length = offset.length()
            outer.setPosition(
                origin.position()
                + Vector3(
                    offset[0] * cos_angle,
                    length * sin_angle,
                    offset[2] * cos_angle,
                )
            )


def correct_rim_edges(node: SopNode) -> None:
    geo = node.geometry()
    for side in (1, -1):
        for index in (2, 3, 4):
            prev_mid, curr_mid, target = points_from_geo(
                geo,
                basesternummiddle(side * (index - 1)),
                basesternummiddle(side * index),
                basesternum(side * index),
            )
            midpoint = (prev_mid.position() + curr_mid.position()) * 0.5
            target.setPosition(midpoint)


def correct_coxa_shape(node: SopNode) -> None:
    geo = node.geometry()

    # Front
    for side in (1, -1):
        target, opposite, sternum_middle, base_middle = points_from_geo(
            geo,
            basesternum(side, 2),
            basesternum(side * 2),
            sternum_attributes.sternumrimmiddle(side),
            basesternummiddle(side),
        )
        pos = reflect_point_across_edge(opposite.position(), (sternum_middle.position(), base_middle.position()))
        target.setPosition(pos)

    # End
    for side, target_minor in ((1, 1), (-1, 2)):
        target, opposite, sternum_middle, base_middle = points_from_geo(
            geo,
            basesternum(5, target_minor),
            basesternum(side * 4),
            sternum_attributes.sternumrimmiddle(side * 4),
            basesternummiddle(side * 4),
        )
        pos = reflect_point_across_edge(opposite.position(), (sternum_middle.position(), base_middle.position()))
        target.setPosition(pos)


def _attrib_new_points(points: Iterable[Point]) -> None:
    for p in points:
        source = p.stringAttribValue("id")
        dest = source.replace(
            sternum_attributes.ID.STERNUMRIMMIDDLE, ID.BASESTERNUMMIDDLE
        ).replace(
            sternum_attributes.ID.STERNUMRIM, ID.BASESTERNUM
        )
        p.setAttribValue("id", dest)


def _attrib_new_prims(prims: Iterable[Prim]) -> None:
    for p in prims:
        if any(p.stringAttribValue("id") == basesternum(0) for p in p.points()):
            p.setAttribValue("region", Region.LABIUM)
        else:
            p.setAttribValue("region", Region.COXA)


def _align_midline_points(geo: Geometry) -> None:
    for p in geo.points():
        if p.stringAttribValue("id") == basesternum(0):
            pos = p.position()
            p.setPosition(Vector3(0.0, pos.y(), pos.z()))


def _split_for_maxilla(geo: Geometry) -> None:
    points = unique_points_by_attrib(geo, "id")
    for i in (1, -1):
        source_pt = points[basesternum(i)]
        labium_pm = next(
            pm
            for pm in source_pt.prims()
            if pm.attribValue("region") == Region.LABIUM
        )
        split_pt, _ = split_point(labium_pm, source_pt)
        split_pt.setAttribValue("id", basesternum(i, 1))
        source_pt.setAttribValue("id", basesternum(i, 2))


def _split_for_pedicel(geo: Geometry) -> None:
    points = unique_points_by_attrib(geo, "id")
    source_pt = points[basesternum(5)]
    left_pm = next(
        pm
        for pm in source_pt.prims()
        if any(pt.stringAttribValue("id") == basesternummiddle(-4) for pt in pm.points())
    )
    split_pt, _ = split_point(left_pm, source_pt)
    split_pt.setAttribValue("id", basesternum(5, 2))
    source_pt.setAttribValue("id", basesternum(5, 1))


def _rotate_single_middle_edge(geo: Geometry, side: int, index: int) -> None:
    start_id, end_id = _rim_edge_ids(side, index)
    p_start, p_end, sternum_middle, base_middle = points_from_geo(
        geo,
        start_id,
        end_id,
        sternum_attributes.sternumrimmiddle(side * index),
        basesternummiddle(side * index),
    )
    sm_pos = sternum_middle.position()
    v = base_middle.position() - sm_pos

    edge = p_end.position() - p_start.position()
    edge_xz = Vector3(edge[0], 0.0, edge[2]).normalized()

    n1 = Vector3(-edge_xz[2], 0.0, edge_xz[0])
    n2 = Vector3(edge_xz[2], 0.0, -edge_xz[0])

    v_xz = Vector3(v[0], 0.0, v[2])
    l_xz = v_xz.length()

    normal = n1 if n1.dot(v_xz) > n2.dot(v_xz) else n2
    v_new = normal * l_xz + Vector3(0.0, v[1], 0.0)

    base_middle.setPosition(sm_pos + v_new)


def _rim_edge_ids(side: int, index: int) -> tuple[str, str]:
    start_idx = side * index
    end_idx = side * (index + 1) if index < 4 else 5
    return sternum_attributes.sternumrim(start_idx), sternum_attributes.sternumrim(end_idx)