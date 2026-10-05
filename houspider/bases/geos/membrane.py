from typing import Sequence

from hou import SopNode, Geometry, Vector3, Prim, Point
from houkit.topologies.basic import offset_point
from houkit.topologies.face_offseter import outset

from houkit_candidate import points_list_by_attrib, direction_and_distance

from houspider.helper import get_control_parms, set_point_id, points_from_geo
from houspider.bases.attributes import (
    Region,
    basecoxamemebrane,
    basecoxamembranemiddle,
    basemaxilla,
    basemaxillamembrane,
    basemouthmembrane,
    basesternum,
    basesternummiddle,
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
    side_ratio, _, _ = get_control_parms(node).membrane_ratio
    points = points_by_id(geo)
    for index in (*range(1, 5), *range(-4, 0)):
        sm = points[sternum_attributes.sternumrimmiddle(index)]
        bsm = points[basesternummiddle(index)]

        dist = sm.position().distanceTo(bsm.position()) * side_ratio
        source_prims = bsm.prims()
        inner_prims = inset_inner_prims(geo, source_prims, dist, use_ratio=False, follow_existing_edge=True)

        _attrib_coxa_membrane_points(inner_prims)

        for prim in inner_prims:
            prim.setAttribValue("region", Region.COXASOCKET)

    for prim in prims_by_attr(geo, "region", Region.COXA):
        prim.setAttribValue("region", Region.COXAMEMBRANE)


def inset_labium(node: SopNode) -> None:
    geo = node.geometry()
    side_ratio, _, _ = get_control_parms(node).membrane_ratio
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
    side_ratio, _, _ = get_control_parms(node).membrane_ratio
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

    ratios = get_control_parms(node).membrane_ratio
    for side in (1, -1):
        for pair in range(1, 5):
            for l, h in ((1, 4), (2, 3)):
                lower, higher = (
                    points[basecoxamemebrane(side * pair, l)],
                    points[basecoxamemebrane(side * pair, h)]
                )
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
    outset(list(geo.prims()), dist, use_ratio=False)
    deduplicate_id_attr(geo)



def _attrib_coxa_membrane_points(
    prims: Sequence[Prim],
) -> None:
    points = points_list_by_attrib(prims, "id")
    for side in (1, -1):
        for number in range(1, 5):
            i = side * number
            _attrib_second(
                points,
                sternum_attributes.sternumrim(i),
                basecoxamemebrane(i, 1),
            )
            _attrib_second(
                points,
                sternum_attributes.sternumrim(i + 1),
                basecoxamemebrane(i, 2),
            )
            _attrib_second(
                points,
                basesternum(i + 1) if i < 4 else basesternum(i, 1 if side > 0 else 2),
                basecoxamemebrane(i, 3),
            )
            _attrib_second(
                points,
                basesternum(i) if i > 1 else basesternum(i, 2),
                basecoxamemebrane(i, 4),
            )
            _attrib_second(
                points,
                sternum_attributes.sternumrimmiddle(i),
                basecoxamembranemiddle(i, 1),
            )
            _attrib_second(
                points,
                basesternummiddle(i),
                basecoxamembranemiddle(i, 2),
            )


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
    ratios: tuple[Vector3, Vector3, Vector3],
) -> None:
    side_ratio, upper_ratio, lower_ratio = ratios
    direction, distance = direction_and_distance(lower, higher)
    unit = distance / (1 - 2 * side_ratio)
    upper_offset = unit * (upper_ratio - side_ratio)
    lower_offset = unit * (lower_ratio - side_ratio)
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

