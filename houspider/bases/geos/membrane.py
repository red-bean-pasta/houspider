from typing import Sequence

from hou import SopNode, Geometry, Vector3, Prim, Point
from houkit.topologies.basic import offset_point
from houkit.topologies.face_offseter import outset

from houkit.attributer import points_list_by_attrib
from houkit.geomath import direction_and_distance

from houspider.helper import get_control_parms, set_point_id, points_from_geo
from houspider.bases.attributes import (
    Region,
    basecoxamemebrane,
    basecoxamembranemiddle,
    baseend,
    basemaxilla,
    basemaxillamembrane,
    basemouthmembrane,
    basesternum,
    basesternummiddle,
    outer_loop_ids,
)
from houspider.helper import (
    deduplicate_id_attr,
    inset_inner_prims,
    move_points,
    points_by_id,
    prims_by_attr,
)
from houspider.sternums import attributes as sternum_attributes


def inset_coxa(node: SopNode) -> None:
    geo = node.geometry()
    side_ratio, _, _ = get_control_parms(node).socket_membrane_ratio
    points = points_by_id(geo)
    for index in (*range(1, 5), *range(-4, 0)):
        sm = points[sternum_attributes.sternumrimmiddle(index)]
        bsm = points[basesternummiddle(index)]

        dist = sm.position().distanceTo(bsm.position()) * side_ratio
        source_prims = bsm.prims()
        inner_prims = inset_inner_prims(geo, source_prims, dist, use_ratio=False, follow_existing_edge=True)

        _attrib_coxa_membrane_points(inner_prims, index)

        for prim in inner_prims:
            prim.setAttribValue("region", Region.COXASOCKET)

    for prim in prims_by_attr(geo, "region", Region.COXA):
        prim.setAttribValue("region", Region.COXAMEMBRANE)


def inset_labium(node: SopNode) -> None:
    geo = node.geometry()
    side_ratio, _, _ = get_control_parms(node).socket_membrane_ratio
    _inset_membrane_region(
        geo,
        side_ratio,
        (sternum_attributes.sternumrim(0), basesternum(0)),
        Region.LABIUM,
        Region.LABIUMSOCKET,
        Region.LABIUMMEMBRANE,
    )
    _classify_labium_membrane_points(geo)


def inset_maxilla(node: SopNode) -> None:
    geo = node.geometry()
    side_ratio, _, _ = get_control_parms(node).socket_membrane_ratio
    _inset_membrane_region(
        geo,
        side_ratio,
        (sternum_attributes.sternumrim(1), basesternum(1, 1)),
        Region.MAXILLA,
        Region.MAXILLASOCKET,
        Region.MAXILLAMEMBRANE,
    )
    _classify_maxilla_membrane_points(geo)



def adjust_coxa_membrane_points(node: SopNode) -> None:
    geo = node.geometry()
    points = points_by_id(geo)

    ratios = get_control_parms(node).socket_membrane_ratio
    for side in (1, -1):
        for pair in range(1, 5):
            index = side * pair
            for lower, higher in (
                (points[basecoxamemebrane(index, 1)], points[basecoxamemebrane(index, 4)]),
                (points[basecoxamemebrane(index, 2)], points[basecoxamemebrane(index, 3)]),
                (points[basecoxamembranemiddle(index, 1)], points[basecoxamembranemiddle(index, 2)]),
            ):
                _offset_vertical_membrane_points(lower, higher, ratios)


def adjust_maxilla_upper_membrane(node: SopNode) -> None:
    geo = node.geometry()
    points = points_by_id(geo)
    for side in (1, -1):
        target_y = points[basecoxamemebrane(side, 4)].position().y()
        lower = points[basemaxillamembrane(side)]
        for index in (2, 3, 4):
            upper = points[basemaxillamembrane(side * index)]
            direction = upper.position() - lower.position()
            move_points((target_y - upper.position().y()) / direction.y(), direction, upper)



def remove_coxa_sockets(node: SopNode) -> None:
    geo = node.geometry()
    socket_prims = prims_by_attr(
        geo,
        "region",
        (Region.COXASOCKET, Region.MAXILLASOCKET),
        startswith=True,
    )
    geo.deletePrims(socket_prims, keep_points=True)



def extrude_base_buffer(node: SopNode) -> None:
    geo = node.geometry()
    sm1, bsm2 = points_from_geo(
        geo,
        sternum_attributes.sternumrimmiddle(1),
        basesternummiddle(1),
    )
    ratio = get_control_parms(node).dorsal_membrane_ratio
    _, baseline = direction_and_distance(sm1, bsm2)
    dist = ratio * baseline
    outer_prims_map = outset(list(geo.prims()), dist, use_ratio=False)
    for prims in outer_prims_map.values():
        for prim in prims:
            prim.setAttribValue("region", Region.BASEBUFFERMEMBRANE)
    deduplicate_id_attr(geo, outer_loop_ids(), keep_first=False)
    _snap_midline_points(geo)


def _snap_midline_points(geo: Geometry) -> None:
    for pid in (basesternum(0), baseend(0)):
        for p in geo.points():
            if p.stringAttribValue("id") == pid:
                pos = p.position()
                p.setPosition(Vector3(0.0, pos.y(), pos.z()))



def _attrib_coxa_membrane_points(
    prims: Sequence[Prim],
    index: int,
) -> None:
    points = {
        p.stringAttribValue("id"): p
        for prim in prims
        for p in prim.points()
        if p.stringAttribValue("id")
    }
    sign = 1 if index > 0 else -1
    next_idx = 5 if abs(index) == 4 else index + sign

    ant_basesternum = basesternum(index, 2) if abs(index) == 1 else basesternum(index)
    post_basesternum = basesternum(5, 1 if index > 0 else 2) if abs(index) == 4 else basesternum(next_idx)

    set_point_id(points[sternum_attributes.sternumrim(index)], basecoxamemebrane(index, 1))
    set_point_id(points[sternum_attributes.sternumrim(next_idx)], basecoxamemebrane(index, 2))
    set_point_id(points[post_basesternum], basecoxamemebrane(index, 3))
    set_point_id(points[ant_basesternum], basecoxamemebrane(index, 4))
    set_point_id(points[sternum_attributes.sternumrimmiddle(index)], basecoxamembranemiddle(index, 1))
    set_point_id(points[basesternummiddle(index)], basecoxamembranemiddle(index, 2))


def _classify_labium_membrane_points(geo: Geometry) -> None:
    pts = points_list_by_attrib(geo, "id", skip_blank=True)
    for side in (1, -1):
        _attrib_second(
            pts,
            sternum_attributes.sternumrim(side),
            basemouthmembrane("lower", side),
        )
        _attrib_second(
            pts,
            basesternum(side, 1),
            basemouthmembrane("upper", side),
        )
    _attrib_second(
        pts,
        sternum_attributes.sternumrim(0),
        basemouthmembrane("lower", 0),
    )
    _attrib_second(
        pts,
        basesternum(0),
        basemouthmembrane("upper", 0),
    )


def _classify_maxilla_membrane_points(geo: Geometry) -> None:
    pts = points_list_by_attrib(geo, "id", skip_blank=True)
    for side in (1, -1):
        for index, name in enumerate(
            (
                sternum_attributes.sternumrim(side),
                basesternum(side, 1),
                basemaxilla(side),
                basesternum(side, 2)
            ),
            start=1
        ):
            _attrib_second(
                pts,
                name,
                basemaxillamembrane(side * index),
            )



def _inset_membrane_region(
    geo: Geometry,
    ratio: float,
    baseline: tuple[str, str],
    source_region: Region,
    socket_region: Region,
    membrane_region: Region,
) -> None:
    inner, outer = points_from_geo(geo, *baseline)
    dist = ratio * inner.position().distanceTo(outer.position())
    prims = prims_by_attr(geo, "region", source_region)
    inner_prims = inset_inner_prims(
        geo,
        prims,
        dist,
        use_ratio=False,
    )
    for prim in inner_prims:
        prim.setAttribValue("region", socket_region)
    for prim in prims_by_attr(geo, "region", source_region):
        prim.setAttribValue("region", membrane_region)


def _offset_vertical_membrane_points(
    lower: Point,
    higher: Point,
    ratios: tuple[float, float, float],
) -> None:
    side_ratio, upper_ratio, lower_ratio = ratios
    direction, distance = direction_and_distance(lower, higher)
    unit = distance / (1 - 2 * side_ratio)
    upper_offset = -direction * (unit * (upper_ratio - side_ratio))
    lower_offset = direction * (unit * (lower_ratio - side_ratio))
    offset_point(lower, lower_offset)
    offset_point(higher, upper_offset)


def _attrib_second(
    points: dict[str, list[Point]],
    source: str, 
    dest: str
) -> None:
    candidates = points[source]
    set_point_id(candidates[1], dest)
    candidates.pop(1)

