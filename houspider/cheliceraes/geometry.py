import hou

from houkit.attributer import add_prim_attrib
from houkit.topology import fill_face
from ..bases import attributes as base_attributes
from ..dorsals.attributes import dorsalbasesupport, dorsalchelicerae
from ..helper import add_id_point, fill_face_with_attr, positions_from_geo, replace_points
from .attributes import Region


def build_geometry(node: hou.SopNode) -> None:
    geo = node.geometry()

    base_ids = (
        base_attributes.basemaxilla(-1),
        base_attributes.basesternum(-1, 1),
        base_attributes.basesternum(0),
        base_attributes.basesternum(1, 1),
        base_attributes.basemaxilla(1),
    )
    base_positions = positions_from_geo(geo, *base_ids)

    upper_ids = tuple(dorsalchelicerae(i) for i in range(-2, 3))
    upper_positions = positions_from_geo(geo, *upper_ids)

    dorsalbase_positions = positions_from_geo(
        geo,
        dorsalbasesupport(dorsalchelicerae(0)),
        dorsalbasesupport(dorsalchelicerae(1)),
        dorsalbasesupport(dorsalchelicerae(2)),
    )

    all_point_data = [
        *zip(base_ids, base_positions),
        *zip(upper_ids, upper_positions),
    ]
    all_points = replace_points(geo, all_point_data)
    base_points = all_points[:len(base_ids)]
    upper_points = all_points[len(base_ids):]
    add_prim_attrib(geo, "region", "")

    fill_face_with_attr(
        geo,
        [
            *base_points,
            *reversed(upper_points),
        ],
        "region",
        Region.CHELICERA,
    )

    _retain_dorsalbase_faces(geo, upper_points[2], upper_points[3], upper_points[4], dorsalbase_positions)


def _retain_dorsalbase_faces(
    geo: hou.Geometry,
    h0: hou.Point,
    h1: hou.Point,
    h2: hou.Point,
    dorsalbase_positions: list[hou.Vector3],
) -> None:
    db0 = add_id_point(geo, dorsalbase_positions[0], dorsalbasesupport(dorsalchelicerae(0)))
    db1 = add_id_point(geo, dorsalbase_positions[1], dorsalbasesupport(dorsalchelicerae(1)))
    db2 = add_id_point(geo, dorsalbase_positions[2], dorsalbasesupport(dorsalchelicerae(2)))

    fill_face([h0, h1, db1, db0])
    fill_face([h1, h2, db2, db1])
