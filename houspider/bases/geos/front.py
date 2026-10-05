import math

from hou import SopNode, Vector3

from houkit_candidate import project_point_on_edge
from houspider.bases.attributes import baseend
from houspider.bases.attributes import basesternum, basemaxilla, Region
from houspider.helper import points_by_id, add_id_point, fill_face_with_region, points_from_geo, positions_from_geo
from houspider.sternums import attributes as sternum_attributes


LABIUM_RATIO = 1/3
MAXILLA_RATIO = ((1 - LABIUM_RATIO) + 1/2) / (1 + (1 - LABIUM_RATIO))


def align_labium(node: SopNode) -> None:
    geo = node.geometry()

    start, end = positions_from_geo(
        geo,
        basesternum(-1, 2),
        basesternum(1, 2),
    )

    for point in points_from_geo(
        geo,
        basesternum(0),
        basesternum(1, 1),
        basesternum(-1, 1),
    ):
        pos = project_point_on_edge(point.position(), (start, end))
        point.setPosition(pos)


def adjust_labium_position(node: SopNode) -> None:
    geo = node.geometry()
    center, left, right, left_end, right_end = points_from_geo(
        geo,
        basesternum(0),
        basesternum(-1, 2),
        basesternum(1, 2),
        basesternum(-1, 1),
        basesternum(1, 1),
    )
    for target, end in ((right, right_end), (left, left_end)):
        target.setPosition(
            end.position() * LABIUM_RATIO
            + center.position() * (1 - LABIUM_RATIO)
        )


def fill_maxilla(node: SopNode) -> None:
    geo = node.geometry()
    points = points_by_id(geo)
    for i in (1, -1):
        start = points[basesternum(i, 1)]
        end = points[basesternum(i, 2)]
        pivot = points[sternum_attributes.sternumrim(-1)]
        maxilla = add_id_point(
            geo,
            start.position() * MAXILLA_RATIO + end.position() * (1 - MAXILLA_RATIO),
            basemaxilla(i),
        )
        fill_face_with_region(
            [start, maxilla, end, pivot],
            Region.MAXILLA,
            i == 1
        )


def fill_pedicel_membrane(node: SopNode) -> None:
    geo = node.geometry()
    s5, e5_1, e5_2 = points_from_geo(
        geo,
        sternum_attributes.sternumrim(5),
        basesternum(5, 1),
        basesternum(5, 2),
    )

    offset = e5_1.position() - s5.position()
    y = offset.y()
    z = math.sqrt(offset.x() ** 2 + offset.z() ** 2)
    e0 = add_id_point(geo, s5.position() + Vector3(0, y, -z), baseend(0))

    fill_face_with_region(
        [e0, e5_1, s5, e5_2],
        Region.BASEPEDICELMEMBRANE
    )
