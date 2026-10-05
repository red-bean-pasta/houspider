import math
from typing import Iterable

from hou import SopNode, Point, Prim, Geometry, Vector3
from houkit.attributings.querier import unique_points_by_attrib, points_from_geo
from houkit.noder import get_parent
from houkit.parameterizer import get_float_parm
from houkit.topology import outset, split_point, offset_point

from houspider.helper import get_control_parms, positions_from_geo
from houspider.houkit_candidate import reflect_point_across_edge
from houspider.bases.attributes import ID, Region, basesternum, basesternummiddle
from houspider.sternums import attributes as sternum_attributes


def extrude_sternum_rim(node: SopNode) -> None:
    geo = node.geometry()
    parent = get_parent(node)
    original_points = set(geo.points())

    flap_ratio = get_float_parm(parent, "coxa_socket_height_ratio")
    island_prims_map = outset(list(geo.prims()), flap_ratio, use_ratio=True)
    assert len(island_prims_map) == 1
    prims = list(island_prims_map.values())[0]
    new_points = [p for p in geo.points() if p not in original_points]

    _attrib_new_points(new_points)
    _attrib_new_prims(prims)
    _split_for_maxilla(geo)
    _split_for_pedicel(geo)


def correct_coxa_shape(node: SopNode) -> None:
    geo = node.geometry()

    # Front
    for side in (1, -1):
        target, opposite, sternum_middle, base_middle = points_from_geo(
            geo,
            basesternum(side, 2),
            basesternum(side * 2, 1),
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
            basesternum(side * 4, 2),
            sternum_attributes.sternumrimmiddle(side * 4),
            basesternummiddle(side * 4),
        )
        pos = reflect_point_across_edge(opposite.position(), (sternum_middle.position(), base_middle.position()))
        target.setPosition(pos)


def rotate_coxa_flaps(node: SopNode) -> None:
    geo = node.geometry()

    params = get_control_parms(node)
    angle = math.radians(params.coxa_socket_rise_angle)
    sin_angle = math.sin(angle)
    cos_angle = math.cos(angle)

    rotated = set()
    for prim in geo.prims():
        points = prim.points()
        for origin, outer in ((points[3], points[0]), (points[2], points[1])):
            if outer.number() in rotated:
                continue
            rotated.add(outer.number())
            offset = outer.position() - origin.position()
            length = offset.length()
            offset_point(
                outer,
                Vector3(
                    offset[0] * cos_angle,
                    length * sin_angle,
                    offset[2] * cos_angle,
                )
            )


def _attrib_new_points(points: Iterable[Point]) -> None:
    for p in points:
        source = p.stringAttribValue("id")
        dest = source.replace(
            sternum_attributes.ID.STERNUMRIM, ID.BASESTERNUM
        ).replace(
            sternum_attributes.ID.STERNUMRIMMIDDLE, ID.BASESTERNUMMIDDLE
        )
        p.setAttribValue("id", dest)


def _attrib_new_prims(prims: Iterable[Prim]) -> None:
    for p in prims:
        if any(p.stringAttribValue("id") == basesternum(0) for p in p.points()):
            p.setAttribValue("region", Region.LABIUM)
        else:
            p.setAttribValue("region", Region.COXA)


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
    split_pt.setAttribValue("id", basesternum(5, 1))
    source_pt.setAttribValue("id", basesternum(5, 2))