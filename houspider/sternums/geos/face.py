from hou import Geometry, Point, SopNode
from houkit.attributer import add_prim_attrib, deduplicate_point_attribs
from houkit.geomath import is_equal_approx
from houkit.topology import inset

from houspider.helper import fill_face_with_region, get_control_parms, points_by_id
from houspider.sternums.attributes import ID, outer_rim_ids, sternumrimmiddle, sternumrim, sternumspine


def build_sternum_faces(node: SopNode) -> None:
    geo = node.geometry()
    points = points_by_id(geo)

    center = [points[sternumrim(0)]] + [points[sternumspine(i)] for i in range(1, 8)] + [points[sternumrim(5)]]
    right = [points[fn(i)] for i in range(1, 5) for fn in (sternumrim, sternumrimmiddle)]
    left = [points[fn(-i)] for i in range(1, 5) for fn in (sternumrim, sternumrimmiddle)]

    _build_base_faces(geo, center, right, left)


def inset_transition_loop(node: SopNode) -> None:
    geo = node.geometry()
    control_params = get_control_parms(node, use_tuple=False)
    ratio_x, _ = control_params.transition_loop_position
    assert 0.0 < ratio_x <= 1.0
    if not is_equal_approx(ratio_x, 1.0):
        inset(list(geo.prims()), 1.0 - ratio_x, use_ratio=True, follow_existing_edge=True)
        deduplicate_point_attribs(geo, "id", outer_rim_ids(), keep_first=True)


def elevate_transition_loop(node: SopNode) -> None:
    geo = node.geometry()
    control_params = get_control_parms(node, use_tuple=False)

    ratio_x, ratio_y = control_params.transition_loop_position
    if is_equal_approx(ratio_x, 1.0):
        return

    ratio, _ = control_params.spine_descent_spec
    depth = control_params.half_width * ratio
    y = -depth * ratio_y
    for point in geo.points():
        point_id = point.stringAttribValue("id")
        if point_id.startswith(outer_rim_ids()) or point_id.startswith(ID.STERNUMSPINE):
            continue
        pos = point.position()
        point.setPosition((pos[0], y, pos[2]))


def _build_base_faces(
    geo: Geometry,
    center: list[Point],
    right: list[Point],
    left: list[Point],
) -> None:
    add_prim_attrib(geo, "region", "")
    for index in range(len(center) - 2):
        fill_face_with_region(
            [center[index], right[index], right[index + 1], center[index + 1]],
            "sternum",
            True,
        )
        fill_face_with_region(
            [center[index], center[index + 1], left[index + 1], left[index]],
            "sternum",
            True,
        )
    fill_face_with_region(
        [center[-2], right[-1], center[-1], left[-1]],
        "sternum",
        True,
    )
