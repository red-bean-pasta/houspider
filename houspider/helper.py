from collections.abc import Callable, Sequence
from typing import Any

from hou import SopNode, Point, Geometry, Polygon, Prim, Vector3, Attrib
from houkit.attributer import (
    add_point_attrib,
    deduplicate_point_attribs,
    modify_point_attribs,
    scan_indexed_attrib_range,
    set_point_attrib,
    set_points_attrib,
    unique_points_by_attrib,
    unique_points_start_with,
)
from houkit import attributer
from houkit.formatter import affix_text
from houkit.noder import sopify, get_control
from houkit.parameterizings.querier import Parameters, get_parms
from houkit.topology import add_point, fill_face, fill_face_by_attrib, inset, offset_point


def affix_id(prefix: str, *affixes: int | str | float) -> str:
    return affix_text(prefix, *affixes)


def add_id_attr(geo: Geometry, default: str = "") -> Attrib:
    return add_point_attrib(geo, "id", default)


def add_id_point(geo: Geometry, position: Vector3, value: str) -> Point:
    return add_point(geo, position, ("id", value))


def get_control_parms(
    node: SopNode,
    exclude_internal: bool = True,
    use_tuple: bool = True,
    control_name: str = "CONTROLS"
) -> Parameters:
    return get_parms(
        get_control(node, control_name),
        exclude_internal,
        use_tuple,
    )


def replace_points(
    geo: Geometry,
    point_data: Sequence[tuple[str, Vector3]],
) -> list[Point]:
    geo.clear()
    add_id_attr(geo)
    return [add_id_point(geo, position, point_id) for point_id, position in point_data]


def fill_face_with_attr(
    points: Sequence[Point],
    attribute: str,
    value: Any,
    reverse: bool = False,
) -> Polygon:
    polygon = fill_face(points, reverse)
    polygon.setAttribValue(attribute, value)
    return polygon

def fill_face_with_region(
    points: Sequence[Point],
    value: Any,
    reverse: bool = False,
) -> Polygon:
    return fill_face_with_attr(points, "region", value, reverse)


def bridge_loops(
    geo: Geometry,
    first_loop: Sequence[Point],
    second_loop: Sequence[Point],
    reverse: bool = False,
    cross_order: bool = False,
    primitive_attr: tuple[str, Any] | None = None,
) -> list[Polygon]:
    assert len(first_loop) == len(second_loop) >= 2, "Expected equally sized loops with at least two points"
    polygons = []
    for index in range(len(first_loop)):
        next_index = (index + 1) % len(first_loop)
        points = (
            [first_loop[next_index], first_loop[index], second_loop[index], second_loop[next_index]]
            if cross_order
            else [first_loop[index], first_loop[next_index], second_loop[next_index], second_loop[index]]
        )
        if primitive_attr is None:
            polygon = fill_face(points, reverse)
        else:
            polygon = fill_face_with_attr(points, primitive_attr[0], primitive_attr[1], reverse)
        polygons.append(polygon)
    return polygons


def prims_by_attr(
    geo: Geometry | Sequence[Prim],
    attribute: str,
    value: str | tuple[str, ...],
    startswith: bool = False,
) -> list[Prim]:
    prims = geo.prims() if hasattr(geo, "prims") else geo
    if startswith:
        return [prim for prim in prims if prim.stringAttribValue(attribute).startswith(value)]
    return [prim for prim in prims if prim.stringAttribValue(attribute) == value]


def set_prim_attr_where_blank(
    geo: Geometry,
    attribute: str,
    value: Any,
) -> None:
    for prim in geo.prims():
        if not prim.stringAttribValue(attribute):
            prim.setAttribValue(attribute, value)


def sopify_chain(
    parent: SopNode,
    input_node: SopNode | None,
    stages: Sequence[Callable[[], None] | Callable[[SopNode], None]],
) -> SopNode:
    current = input_node
    for stage in stages:
        current = sopify(parent, current, stage)
    assert current is not None, "Expected a chain with at least one stage"
    return current


def move_points(
    ratio: float,
    direction: Vector3,
    *points: Point,
) -> None:
    offset = direction * ratio
    for point in points:
        offset_point(point, offset)


def points_from_loop_cut(
    cut_edges: dict[tuple[Point, Point], tuple[Prim, Prim]],
) -> list[Point]:
    edges = list(cut_edges)
    if not edges:
        return []

    points = [edges[0][0]]
    for start, end in edges:
        assert points[-1] == start, "Loop cut edges are not ordered"
        points.append(end)
    if points[-1] == points[0]:
        points.pop()
    return points


def inset_inner_prims(
    geo: Geometry,
    prims: list[Prim],
    scalar: float,
    use_ratio: bool = True,
    follow_existing_edge: bool = True,
) -> list[Prim]:
    if not prims or scalar == 0:
        return list(prims)

    prim_count_before = len(geo.prims())
    components = inset(prims, scalar, use_ratio, follow_existing_edge)
    created_prims = list(geo.prims())[prim_count_before - len(prims):]

    inner_prims: list[Prim] = []
    created_index = 0
    for inner_component, border_prims in components.items():
        inner_count = len(inner_component)
        inner_prims.extend(created_prims[created_index:created_index + inner_count])
        created_index += inner_count + len(border_prims)

    assert created_index == len(created_prims), "Unexpected inset primitive layout"
    return inner_prims


def points_by_id(
    geo: Geometry | Prim | Sequence[Prim],
) -> dict[str, Point]:
    return unique_points_by_attrib(geo, "id")


def points_from_geo(geo: Geometry, *ids: str) -> tuple[Point, ...]:
    return tuple(attributer.points_from_geo(geo, "id", *ids))

def positions_from_geo(geo: Geometry, *ids: str) -> tuple[Vector3, ...]:
    return tuple(attributer.positions_from_geo(geo, "id", *ids))

def positions_from_points(*points: Point) -> tuple[Vector3, ...]:
    return tuple(p.position() for p in points)


def set_point_id(point: Point, value: str) -> None:
    set_point_attrib(point, "id", value)


def set_points_id(points: Sequence[Point], values: Sequence[str]) -> None:
    set_points_attrib(points, "id", values)


def get_id_range(geo: Geometry, prefix: str) -> tuple[int, int] | None:
    return scan_indexed_attrib_range(geo, "id", prefix)


def fill_face_by_id(geo: Geometry, values: Sequence[str], reverse: bool = False) -> Polygon:
    return fill_face_by_attrib(geo, "id", values, reverse)


def fill_face_by_id_with_attr(
    geo: Geometry,
    values: Sequence[str],
    attribute: str,
    value: Any,
    reverse: bool = False,
) -> Polygon:
    polygon = fill_face_by_id(geo, values, reverse)
    polygon.setAttribValue(attribute, value)
    return polygon


def unique_points_start_with_id(
    geo: Geometry,
    prefixes: str | tuple[str, ...],
) -> dict[str, Point]:
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    return {
        point_id: point
        for points in unique_points_start_with(geo, "id", prefixes).values()
        for point_id, point in points.items()
    }


def deduplicate_id_attr(
    geo: Geometry,
    prefix: str | tuple[str, ...] | None = None,
    add_affix: bool = False,
    keep_first: bool = True,
) -> None:
    deduplicate_point_attribs(geo, "id", prefix, add_affix=add_affix, keep_first=keep_first)


def rename_left_ids(geo: Geometry, affix_index: int | None = 0) -> None:
    """Rename point IDs for mirrored geometry on the left side (x < 0).

    Negates the numeric affix at the given `affix_index`.
    `affix_index` can be negative to index from the last.
    Use None to negate all affixes.
    `affix_index` defaults to 0.
    """
    modify_point_attribs(
        geo,
        "id",
        _is_left_point,
        lambda point_id: _rename_point_id(point_id, affix_index),
    )

def _is_left_point(point: Point) -> bool:
    return point.position()[0] < 0.0

def _rename_point_id(point_id: str, affix_index: int | None) -> str | None:
    parts = point_id.split("_")
    first_digit = next(
        (index for index, character in enumerate(parts[0]) if character.isdigit() or character == "-"),
        None,
    )
    if first_digit is not None:
        prefix = parts[0][:first_digit]
        affixes = [parts[0][first_digit:]] + parts[1:]
    elif len(parts) > 1:
        prefix = parts[0] + "_"
        affixes = parts[1:]
    else:
        return None

    if affix_index is None:
        affixes = [_negate_id_affix(affix) for affix in affixes]
    else:
        try:
            affixes[affix_index] = _negate_id_affix(affixes[affix_index])
        except IndexError:
            if len(affixes) == 1:
                affixes[0] = _negate_id_affix(affixes[0])

    return prefix + "_".join(affixes)

def _negate_id_affix(value: str) -> str:
    if not value:
        return value
    return value[1:] if value.startswith("-") else f"-{value}"


def rename_left_ids_node(node: SopNode) -> None:
    rename_left_ids(node.geometry())


def compute_rest_flex_angles(
    min_flex: Sequence[float],
    max_flex: Sequence[float],
    ratios: Sequence[float],
) -> tuple[float, ...]:
    return tuple(lo + r * (hi - lo) for lo, hi, r in zip(min_flex, max_flex, ratios))


def update_joint_limits(
    geo: Geometry,
    pattern: str,
    min_flex: Sequence[float],
    max_flex: Sequence[float],
    min_yaw: Sequence[float],
    max_yaw: Sequence[float],
    rest_ratios: Sequence[float],
) -> None:
    from .attributes import GlobalAttrib
    import hou

    rest_flex = compute_rest_flex_angles(min_flex, max_flex, rest_ratios)
    limits_dict = {
        "min_flex_angles": tuple(min_flex),
        "max_flex_angles": tuple(max_flex),
        "min_yaw_angles": tuple(min_yaw),
        "max_yaw_angles": tuple(max_yaw),
        "rest_flex_ratios": tuple(rest_ratios),
        "rest_flex_angles": rest_flex,
    }
    attrib = geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS)
    if attrib:
        cur_limits = dict(geo.dictAttribValue(attrib))
    else:
        cur_limits = {}
        attrib = geo.addAttrib(hou.attribType.Global, GlobalAttrib.JOINT_LIMITS, {})
    cur_limits[pattern] = limits_dict
    geo.setGlobalAttribValue(attrib, cur_limits)

