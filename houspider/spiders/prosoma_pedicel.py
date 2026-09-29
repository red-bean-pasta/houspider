import hou

from houkit.noder import get_parent
from houkit.parameterizer import get_parms
from houkit.topology import fill_face, fill_pentagon, offset_point
from .attributes import prosomapedicelleft, prosomapedicelright, prosomapedicelupper, prosomapedicellower
from ..bases import attributes as base_attributes
from ..dorsals import attributes as dorsal_attributes
from ..helper import add_id_point, fill_face_with_attr, points_from_geo, prims_by_attr, set_prim_attr_where_blank
from ..sternums import attributes as sternum_attributes


def open_prosoma_pedicel(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    parent = get_parent(node)
    params = get_parms(parent)
    pedicel_opening_ratios = params.pedicel_opening_ratios
    pedicel_opening_ratio_x, _ = pedicel_opening_ratios

    (
        baseend0,
        basesupportend0,
        dorsalsupport4,
        dorsalsupport_minus4,
        dorsalsupport5,
        sternumrim5,
        bs5_1,
        bs5_2,
        basesupportsternum5_1,
        basesupportsternum5_2,
    ) = points_from_geo(
        geo,
        base_attributes.baseend(0),
        dorsal_attributes.dorsalbasesupport(base_attributes.baseend(0)),
        dorsal_attributes.dorsalsupport(4),
        dorsal_attributes.dorsalsupport(-4),
        dorsal_attributes.dorsalsupport(5),
        sternum_attributes.sternumrim(5),
        base_attributes.basesternum(5, 1),
        base_attributes.basesternum(5, 2),
        dorsal_attributes.dorsalbasesupport(base_attributes.basesternum(5, 1)),
        dorsal_attributes.dorsalbasesupport(base_attributes.basesternum(5, 2)),
    )

    support_loop_width = _get_opening_support_loop_width(bs5_1, bs5_2, pedicel_opening_ratio_x)

    pp_outer_lower, right_inner, left_inner = _identify_pedicel_membrane_points(geo)
    pp_right, pp_left, pp_outer_right, pp_outer_left = _add_side_prosoma_pedicel_points(
        geo, baseend0, bs5_1, bs5_2, pedicel_opening_ratio_x, support_loop_width
    )
    pp_upper, pp_lower = _position_vertical_pedicel_points(
        geo, baseend0, basesupportend0, dorsalsupport5, sternumrim5, pp_outer_lower, pedicel_opening_ratios, support_loop_width
    )
    _reconnect_lower_sternum_pedicel_loop(
        geo,
        pp_lower,
        pp_outer_lower,
        pp_right,
        pp_outer_right,
        pp_left,
        pp_outer_left,
        left_inner,
        right_inner,
        bs5_1,
        bs5_2,
        sternumrim5,
    )
    p_right, p_left = _reconnect_upper_sternum_pedicel_loop(
        geo,
        baseend0,
        basesupportend0,
        basesupportsternum5_1,
        basesupportsternum5_2,
        pp_upper,
        pp_right,
        pp_outer_right,
        pp_left,
        pp_outer_left,
        bs5_1,
        bs5_2,
        pedicel_opening_ratio_x,
    )
    _retopo_dorsal_back_faces(
        geo,
        dorsalsupport4,
        dorsalsupport_minus4,
        dorsalsupport5,
        basesupportend0,
        basesupportsternum5_1,
        basesupportsternum5_2,
        p_right,
        p_left,
    )
    _adjust_opening_points_depth(pp_right, pp_left, pp_upper)

def _get_opening_support_loop_width(
    bs5_1: hou.Point,
    bs5_2: hou.Point,
    pedicel_opening_ratio_x: float,
) -> float:
    return bs5_1.position().x() * (1.0 - pedicel_opening_ratio_x) * 0.035


def _identify_pedicel_membrane_points(geo: hou.Geometry) -> tuple[hou.Point, hou.Point, hou.Point]:
    membrane_prims = prims_by_attr(geo, "region", base_attributes.Region.BASEPEDICELMEMBRANE)
    assert len(membrane_prims) == 1, f"Expected 1 basepedicelmembrane prim, got {len(membrane_prims)}"
    mem_prim = membrane_prims[0]

    p_lower = None
    right_inner = None
    left_inner = None
    for pt in mem_prim.points():
        pt_id = pt.stringAttribValue("id")
        if pt_id == sternum_attributes.sternumrim(5):
            continue
        if abs(pt.position().x()) < 1e-4:
            p_lower = pt
        elif pt.position().x() > 0:
            right_inner = pt
        else:
            left_inner = pt

    assert p_lower is not None, "Expected lower p point in basepedicelmembrane"
    assert right_inner is not None, "Expected right inner point in basepedicelmembrane"
    assert left_inner is not None, "Expected left inner point in basepedicelmembrane"
    return p_lower, right_inner, left_inner


def _add_side_prosoma_pedicel_points(
    geo: hou.Geometry,
    baseend0: hou.Point,
    bs5_1: hou.Point,
    bs5_2: hou.Point,
    size_ratio_x: float,
    support_width: float,
) -> tuple[hou.Point, hou.Point, hou.Point, hou.Point]:
    p_end = baseend0.position()
    pos_bs5_1 = bs5_1.position()
    pos_bs5_2 = bs5_2.position()

    dir_right = (pos_bs5_1 - p_end).normalized()
    dir_left = (pos_bs5_2 - p_end).normalized()

    pos_right = pos_bs5_1 * size_ratio_x + p_end * (1 - size_ratio_x)
    pos_outer_right = pos_right + dir_right * support_width

    # pp = prosoma pedicel
    pp_right = add_id_point(geo, pos_right, prosomapedicelright())

    pp_outer_right = geo.createPoint()
    pp_outer_right.setPosition(pos_outer_right)

    pos_left = pos_bs5_2 * size_ratio_x + p_end * (1 - size_ratio_x)
    pos_outer_left = pos_left + dir_left * support_width

    pp_left = add_id_point(geo, pos_left, prosomapedicelleft())

    pp_outer_left = geo.createPoint()
    pp_outer_left.setPosition(pos_outer_left)

    return pp_right, pp_left, pp_outer_right, pp_outer_left


def _position_vertical_pedicel_points(
    geo: hou.Geometry,
    baseend0: hou.Point,
    basesupportend0: hou.Point,
    dorsalsupport5: hou.Point,
    sternumrim5: hou.Point,
    pp_outer_lower: hou.Point,
    pedicel_opening_ratios: tuple[float, float],
    support_width: float,
) -> tuple[hou.Point, hou.Point]:
    _, ratio_y = pedicel_opening_ratios

    p_end = baseend0.position()
    p_dorsal = dorsalsupport5.position()
    p_sternum = sternumrim5.position()

    dir_upper = (p_dorsal - p_end).normalized()

    pos_pp_lower = p_sternum * ratio_y + p_end * (1 - ratio_y)
    pos_pp_outer_lower = p_sternum * (1.0 / 3.0) + pos_pp_lower * (2.0 / 3.0)
    pp_outer_lower.setPosition(pos_pp_outer_lower)

    pp_lower = add_id_point(geo, pos_pp_lower, prosomapedicellower())

    target_height = p_end.y() - pos_pp_lower.y()
    dy = p_dorsal.y() - p_end.y()
    assert abs(dy) > 1e-6, "Expected non-zero y delta between baseend0 and dorsalback0"
    t = target_height / dy
    offset = t * (p_dorsal - p_end)
    p_upper = p_end + offset
    pos_baseend0 = p_upper + dir_upper * support_width
    baseend0_offset = pos_baseend0 - p_end

    pp_upper = add_id_point(geo, p_upper, prosomapedicelupper())

    baseend0.setPosition(pos_baseend0)
    offset_point(basesupportend0, baseend0_offset)

    return pp_upper, pp_lower


def _reconnect_lower_sternum_pedicel_loop(
    geo: hou.Geometry,
    pp_lower: hou.Point,
    pp_outer_lower: hou.Point,
    pp_right: hou.Point,
    pp_outer_right: hou.Point,
    pp_left: hou.Point,
    pp_outer_left: hou.Point,
    left_inner: hou.Point,
    right_inner: hou.Point,
    bs5_1: hou.Point,
    bs5_2: hou.Point,
    s5: hou.Point,
) -> None:
    p_prims = list(pp_outer_lower.prims())
    geo.deletePrims(p_prims, keep_points=True)

    fill_pentagon([pp_outer_right, bs5_1, right_inner, s5, pp_outer_lower], (pp_outer_lower, s5), reverse_order=True)
    fill_pentagon([pp_outer_left, bs5_2, left_inner, s5, pp_outer_lower], (pp_outer_lower, s5), reverse_order=False)

    fill_face([pp_lower, pp_right, pp_outer_right, pp_outer_lower], reverse_order=False)
    fill_face([pp_lower, pp_left, pp_outer_left, pp_outer_lower], reverse_order=True)


def _reconnect_upper_sternum_pedicel_loop(
    geo: hou.Geometry,
    baseend0: hou.Point,
    basesupportend0: hou.Point,
    basesupportsternum5_1: hou.Point,
    basesupportsternum5_2: hou.Point,
    pp_upper: hou.Point,
    pp_right: hou.Point,
    pp_outer_right: hou.Point,
    pp_left: hou.Point,
    pp_outer_left: hou.Point,
    bs5_1: hou.Point,
    bs5_2: hou.Point,
    size_ratio_x: float,
) -> tuple[hou.Point, hou.Point]:
    _remove_upper_dorsal_back_faces(baseend0, geo)
    p_right, p_left = _create_upper_pedicel_support_points(
        geo,
        baseend0,
        basesupportend0,
        basesupportsternum5_1,
        basesupportsternum5_2,
        pp_outer_right,
        pp_outer_left,
        bs5_1,
        bs5_2,
        size_ratio_x,
    )
    _fill_upper_pedicel_dorsal_back_faces(
        geo,
        basesupportend0,
        baseend0,
        pp_outer_right,
        p_right,
        bs5_1,
        basesupportsternum5_1,
        pp_outer_left,
        p_left,
        bs5_2,
        basesupportsternum5_2,
    )
    _fill_upper_pedicel_buffer_faces(geo, pp_upper, pp_right, pp_left, pp_outer_right, pp_outer_left, baseend0)
    return p_right, p_left


def _remove_upper_dorsal_back_faces(baseend0: hou.Point, geo: hou.Geometry) -> None:
    dorsalback_prims = prims_by_attr(baseend0.prims(), "region", dorsal_attributes.Region.DORSALBACK)
    assert len(dorsalback_prims) == 2, f"Expected 2 dorsalback prims on baseend0, got {len(dorsalback_prims)}"
    geo.deletePrims(dorsalback_prims, keep_points=True)


def _create_upper_pedicel_support_points(
    geo: hou.Geometry,
    baseend0: hou.Point,
    basesupportend0: hou.Point,
    basesupportsternum5_1: hou.Point,
    basesupportsternum5_2: hou.Point,
    pp_outer_right: hou.Point,
    pp_outer_left: hou.Point,
    bs5_1: hou.Point,
    bs5_2: hou.Point,
    size_ratio_x: float,
) -> tuple[hou.Point, hou.Point]:
    v_end = basesupportend0.position() - baseend0.position()
    v_bs1 = basesupportsternum5_1.position() - bs5_1.position()
    v_bs2 = basesupportsternum5_2.position() - bs5_2.position()

    pos_p_right = pp_outer_right.position() + v_bs1 * size_ratio_x + v_end * (1 - size_ratio_x)
    pos_p_left = pp_outer_left.position() + v_bs2 * size_ratio_x + v_end * (1 - size_ratio_x)

    p_right = geo.createPoint()
    p_right.setPosition(pos_p_right)

    p_left = geo.createPoint()
    p_left.setPosition(pos_p_left)

    return p_right, p_left


def _fill_upper_pedicel_dorsal_back_faces(
    geo: hou.Geometry,
    basesupportend0: hou.Point,
    baseend0: hou.Point,
    pp_outer_right: hou.Point,
    p_right: hou.Point,
    bs5_1: hou.Point,
    basesupportsternum5_1: hou.Point,
    pp_outer_left: hou.Point,
    p_left: hou.Point,
    bs5_2: hou.Point,
    basesupportsternum5_2: hou.Point,
) -> None:
    # Reconnect upper-right and upper-left faces
    fill_face_with_attr(
        geo, [basesupportend0, baseend0, pp_outer_right, p_right], "region", dorsal_attributes.Region.DORSALBACK, reverse=True
    )
    fill_face_with_attr(
        geo, [p_right, pp_outer_right, bs5_1, basesupportsternum5_1], "region", dorsal_attributes.Region.DORSALBACK, reverse=True
    )
    fill_face_with_attr(
        geo, [basesupportend0, baseend0, pp_outer_left, p_left], "region", dorsal_attributes.Region.DORSALBACK, reverse=False
    )
    fill_face_with_attr(
        geo, [p_left, pp_outer_left, bs5_2, basesupportsternum5_2], "region", dorsal_attributes.Region.DORSALBACK, reverse=False
    )


def _fill_upper_pedicel_buffer_faces(
    geo: hou.Geometry,
    pp_upper: hou.Point,
    pp_right: hou.Point,
    pp_left: hou.Point,
    pp_outer_right: hou.Point,
    pp_outer_left: hou.Point,
    baseend0: hou.Point,
) -> None:
    fill_face_with_attr(
        geo, [pp_upper, pp_right, pp_outer_right, baseend0], "region", base_attributes.Region.BASEBUFFERMEMBRANE, reverse=True
    )
    fill_face_with_attr(
        geo, [pp_upper, pp_left, pp_outer_left, baseend0], "region", base_attributes.Region.BASEBUFFERMEMBRANE, reverse=False
    )


def _retopo_dorsal_back_faces(
    geo: hou.Geometry,
    dorsalsupport4: hou.Point,
    dorsalsupport_minus4: hou.Point,
    dorsalsupport5: hou.Point,
    basesupportend0: hou.Point,
    basesupportsternum5_1: hou.Point,
    basesupportsternum5_2: hou.Point,
    p_right: hou.Point,
    p_left: hou.Point,
) -> None:
    prims_to_delete = [
        pr for pr in dorsalsupport5.prims()
        if pr.stringAttribValue("region") == dorsal_attributes.Region.DORSALBACK and basesupportend0 in pr.points()
    ]
    assert len(prims_to_delete) == 2, f"Expected 2 upper dorsalback prims on dorsalsupport5, got {len(prims_to_delete)}"
    geo.deletePrims(prims_to_delete, keep_points=True)

    fill_pentagon(
        [dorsalsupport4, dorsalsupport5, basesupportend0, p_right, basesupportsternum5_1],
        (dorsalsupport5, basesupportend0),
        reverse_order=False,
    )
    fill_pentagon(
        [dorsalsupport_minus4, dorsalsupport5, basesupportend0, p_left, basesupportsternum5_2],
        (dorsalsupport5, basesupportend0),
        reverse_order=True,
    )

    set_prim_attr_where_blank(geo, "region", dorsal_attributes.Region.DORSALBACK)


def _adjust_opening_points_depth(
    pp_right: hou.Point,
    pp_left: hou.Point,
    pp_upper: hou.Point,
) -> None:
    offset_z = (pp_right.position().x() - pp_left.position().x()) / 4.0
    offset = hou.Vector3(0.0, 0.0, -offset_z)
    for pt in (pp_right, pp_left, pp_upper):
        offset_point(pt, offset)
