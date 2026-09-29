import hou

from ..bases import attributes as base_attributes
from ..helper import fill_face_by_id_with_attr, points_from_geo, set_point_id, set_prim_attr_where_blank
from houkit.attributer import add_prim_attrib
from houkit.topology import fill_pentagon, offset_point
from .attributes import Region, dorsalback, dorsalchelicerae, dorsalfront, dorsalfrontfloat, dorsalfrontmid, dorsaltopmiddle, dorsalsupport
from .helper import get_dorsal_base_loop_width

def add_dorsal_dent(node: hou.SopNode) -> None:
    geo = node.geometry()
    dorsalfront0, dorsalsupport0 = points_from_geo(
        geo,
        dorsalfront(0),
        dorsalsupport(0),
    )
    dist = dorsalfront0.position().distanceTo(dorsalsupport0.position())
    direction = (dorsalsupport0.position() - dorsalfront0.position()).normalized()
    offset = direction * (dist * 1/3)
    offset_point(dorsalfront0, offset)
    offset_point(dorsalsupport0, offset)


def curve_lip(node: hou.SopNode) -> None:
    geo = node.geometry()
    dist = get_dorsal_base_loop_width(node)
    dorsalchelicerae1, dorsalsupport1 = points_from_geo(geo, dorsalchelicerae(1), dorsalsupport(1))
    offset = hou.Vector3(0.0, dist * 2, 0.0)
    for point in (dorsalchelicerae1, dorsalsupport1):
        offset_point(point, offset)


def fill_back_loop_faces(node: hou.SopNode) -> None:
    geo = node.geometry()
    add_prim_attrib(geo, "region", "")

    _fill_dorsal_front_faces(geo)
    _add_dorsal_front_pentagon(geo)
    _fill_dorsal_top_and_back_faces(geo)
    set_prim_attr_where_blank(geo, "region", Region.DORSALTOP)


def _fill_dorsal_front_faces(geo: hou.Geometry) -> None:
    fill_face_by_id_with_attr(
        geo,
        (
            dorsalchelicerae(0),
            dorsalsupport(0),
            dorsalsupport(1),
            dorsalchelicerae(1),
        ),
        "region",
        Region.DORSALFRONTMAIN,
        True,
    )

    fill_face_by_id_with_attr(
        geo,
        (
            dorsalchelicerae(1),
            dorsalsupport(1),
            dorsalsupport(2),
            dorsalchelicerae(2),
        ),
        "region",
        Region.DORSALFRONTMAIN,
        True,
    )

    fill_face_by_id_with_attr(
        geo,
        (
            dorsalchelicerae(2),
            dorsalsupport(2),
            base_attributes.basesternum(1, 2),
            base_attributes.basemaxilla(1),
        ),
        "region",
        Region.DORSALFRONTCHEEK,
        True,
    )


def _add_dorsal_front_pentagon(geo: hou.Geometry) -> None:
    hf0, hf1, hs2, hs1, hs0 = points_from_geo(
        geo,
        dorsalfront(0),
        dorsalfront(1),
        dorsalsupport(2),
        dorsalsupport(1),
        dorsalsupport(0),
    )
    midpoint, floatpoint = fill_pentagon(
        [hf0, hf1, hs2, hs1, hs0],
        (hf0, hs0),
    )
    set_point_id(midpoint, dorsalfrontmid(0))
    set_point_id(floatpoint, dorsalfrontfloat(1))


def _fill_dorsal_top_and_back_faces(geo: hou.Geometry) -> None:
    faces = {
        (
            dorsalfront(0),
            dorsalfront(1),
            dorsaltopmiddle(1),
            dorsaltopmiddle(0),
        ): (False, Region.DORSALTOP),
        (
            dorsaltopmiddle(0),
            dorsaltopmiddle(1),
            dorsalback(1),
            dorsalback(0),
        ): (False, Region.DORSALTOP),
        (
            dorsalback(1),
            dorsalback(0),
            dorsalsupport(5),
            dorsalsupport(4),
        ): (True, Region.DORSALTOP),
        (
            dorsalsupport(4),
            dorsalsupport(5),
            base_attributes.baseend(0),
            base_attributes.basesternum(5, 1),
        ): (True, Region.DORSALBACK),
    }

    for face, (reverse, region) in faces.items():
        fill_face_by_id_with_attr(geo, face, "region", region, reverse)


def fill_support_loop_faces(node: hou.SopNode) -> None:
    geo = node.geometry()
    faces = {
        (
            dorsalfront(1),
            dorsaltopmiddle(1),
            dorsalsupport(3),
            dorsalsupport(2),
        ): True,
        (
            dorsaltopmiddle(1),
            dorsalback(1),
            dorsalsupport(4),
            dorsalsupport(3),
        ): True,
    }
    regions = (Region.DORSALTOP, Region.DORSALTOP)

    for i, (face, reverse) in enumerate(faces.items()):
        fill_face_by_id_with_attr(geo, face, "region", regions[i], reverse)
