import hou

from houkit.topologies.basic import remove_unused_points
from houkit.attributer import points_by_attrib
from houkit.noder import get_parent
from houkit.parameterizer import get_parms
from houkit.topology import inset, offset_point

from ..helper import deduplicate_id_attr, points_from_geo, set_point_id
from .attributes import dorsalbasesupport, dorsalchelicerae, dorsalfront, dorsalfrontfloat, dorsalfrontmid, dorsalsupport
from .helper import get_dorsal_base_loop_width

def inset_base_support_loop(node: hou.SopNode) -> None:
    geo = node.geometry()
    dist = get_dorsal_base_loop_width(node)
    inset(list(geo.prims()), dist, use_ratio=False)
    _attribute_inset_points(geo)
    deduplicate_id_attr(geo, None, keep_first=True)

def _attribute_inset_points(geo: hou.Geometry) -> None:
    points = points_by_attrib(geo, "id", True)
    for point_id, matching in points.items():
        if not point_id or len(matching) != 2:
            continue
        inset_pt = max(matching, key=lambda pt: pt.number())
        set_point_id(inset_pt, dorsalbasesupport(point_id))


def extrude_lip(node: hou.SopNode) -> None:
    geo = node.geometry()
    parent = get_parent(node)
    ratio_x, ratio_y = get_parms(parent).lip_extrusion_ratio

    # d0: dorsalbasesupport(0), c0: dorsalchelicerae(0)
    d0, c0 = points_from_geo(
        geo,
        dorsalbasesupport(dorsalchelicerae(0)),
        dorsalchelicerae(0),
    )
    baseline = d0.position().y() - c0.position().y()

    z_offset = -baseline * ratio_x
    y_offset = -baseline * ratio_y
    offset = hou.Vector3(0.0, y_offset, z_offset)

    for side in (0, 1, 2, -1, -2):
        # dc: dorsalchelicerae, db: dorsalbasesupport, ds: dorsalsupport
        dc, db, ds = points_from_geo(
            geo,
            dorsalchelicerae(side),
            dorsalbasesupport(dorsalchelicerae(side)),
            dorsalsupport(side),
        )
        for pt in (dc, db, ds):
            offset_point(pt, offset)

    for side in (0, 1, -1):
        (hf,) = points_from_geo(geo, dorsalfront(side))
        offset_point(hf, offset)

    for side in (1, -1):
        (hff,) = points_from_geo(geo, dorsalfrontfloat(side))
        offset_point(hff, offset)

    (hfm,) = points_from_geo(geo, dorsalfrontmid(0))
    offset_point(hfm, offset)


def cleanup(node: hou.SopNode) -> None:
    geo = node.geometry()
    remove_unused_points(geo)
