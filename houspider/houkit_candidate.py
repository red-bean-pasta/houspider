from typing import Sequence

from hou import Vector3, Geometry, Prim, Point
from houkit.attributings.querier import points_by_attrib


def direction_and_distance(
    source: Point,
    target: Point,
) -> tuple[Vector3, float]:
    pt = target.position()
    ps = source.position()
    return (
        (pt - ps).normalized(),
        ps.distanceTo(pt),
    )


def points_list_by_attrib(
    source: Geometry | Prim | Sequence[Prim],
    attribute: str,
    skip_blank: bool = False,
) -> dict[str, list[Point]]:
    points = points_by_attrib(source, attribute, skip_blank)
    result: dict[str, list[Point]] = {}
    for k, v in points.items():
        result[k] = sorted(v, key=lambda p: p.number())
    return result


def reflect_point_across_edge(
    point: Vector3,
    edge: tuple[Vector3, Vector3],
) -> Vector3:
    start, end = edge
    vector = end - start
    length_squared = vector.dot(vector)
    offset = point - start
    projection = start + vector * (offset.dot(vector) / length_squared)
    return projection * 2.0 - point


def project_point_on_edge(
    target: Vector3,
    edge: tuple[Vector3, Vector3],
) -> Vector3:
    start, end = edge
    direction = end - start
    length_squared = direction.dot(direction)
    offset = target - start
    return start + direction * (offset.dot(direction) / length_squared)
