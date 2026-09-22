from typing import Collection

from hou import Geometry, Point, Prim, Vector3
from houkit.attributings.querier import points_start_with
from houkit.topologies.helper import is_neighbor

from houspider.bases.attributes import basecoxamemebrane, basemaxillamembrane
from ..segments.attributes import Region


def get_coxa_socket_points(
    geo: Geometry,
    is_right: bool,
    index: int,
) -> list[Point]:
    prefix = f"{basecoxamemebrane(index if is_right else -index)}_"
    return points_start_with(geo, "id", prefix)


def get_pedipalp_socket_points(
    geo: Geometry,
    is_right: bool,
) -> list[Point]:
    left_pts = points_start_with(geo, "id", basemaxillamembrane("-"))
    socket_pts = [
        p
        for p in points_start_with(geo, "id", basemaxillamembrane())
        if p not in left_pts
    ] if is_right else left_pts
    return socket_pts


def traverse_limb_prims(
    socket_pts: list[Point],
) -> tuple[set[Prim], set[Point]]:
    visited_prims: set[Prim] = set()
    visited_pts: set[Point] = set(socket_pts)

    queue: list[Point] = list(socket_pts)
    while queue:
        pt = queue.pop(0)
        for prim in pt.prims():
            if prim in visited_prims:
                continue
            region = prim.stringAttribValue("region")
            if region in (Region.LEGSEGMENT, Region.LEGMEMBRANE):
                visited_prims.add(prim)
                for p in prim.points():
                    if p not in visited_pts:
                        visited_pts.add(p)
                        queue.append(p)

    return visited_prims, visited_pts


def group_membrane_rings(
    prims: set[Prim],
) -> list[tuple[set[Prim], set[Point]]]:
    membranes = [p for p in prims if p.stringAttribValue("region") == Region.LEGMEMBRANE]

    rings: list[tuple[set[Prim], set[Point]]] = []
    visited: set[Prim] = set()
    for prim in membranes:
        if prim in visited:
            continue
        queue = [prim]
        comp_prims: set[Prim] = set()
        visited.add(prim)
        while queue:
            cur = queue.pop()
            comp_prims.add(cur)
            for pt in cur.points():
                for nbr in pt.prims():
                    if nbr in membranes and nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
        ring_pts = set({pt for p in comp_prims for pt in p.points()})
        rings.append((comp_prims, ring_pts))

    rings = sorted(
        rings,
        key=lambda ring: min(
            abs(point.position().x())
            for point in ring[1]
        ),
    )
    return rings


def get_local_z_direction(
    membrane_points: Collection[Point],
) -> Vector3:
    loop1, loop2 = get_membrane_boundaries(membrane_points)
    m1 = sum((p.position() for p in loop1), Vector3()) / 4.0
    m2 = sum((p.position() for p in loop2), Vector3()) / 4.0
    former, latter = (m1, m2) if m1.length() < m2.length() else (m2, m1)
    direction = (latter - former).normalized()
    return Vector3(direction.x(), 0.0, direction.z()).normalized()


def get_local_z_value(
    target: Point | Vector3,
    direction: Vector3,
) -> float:
    pos = target.position() if isinstance(target, Point) else target
    return pos.dot(direction)


def get_membrane_boundaries(
    membrane_points: Collection[Point],
) -> tuple[list[Point], list[Point]]:
    assert len(membrane_points) > 12
    boundaries = [
        p
        for p in membrane_points
        if any(pr.stringAttribValue("region") == Region.LEGSEGMENT for pr in p.prims())
    ]
    assert len(boundaries) == 8, f"Expected 8 boundary points on membrane ring, got {len(boundaries)}"

    p0 = boundaries[0]
    direct_neighbors = [p for p in boundaries if is_neighbor(p, p0)]
    loop1 = [
        p
        for p in boundaries
        if p == p0 or p in direct_neighbors or any(is_neighbor(p, n) for n in direct_neighbors)
    ]
    loop2 = [
        p
        for p in boundaries
        if p not in loop1
    ]
    assert len(loop1) == 4 and len(loop2) == 4, f"Expected 4 points per loop, got {len(loop1)} and {len(loop2)}"

    loop1, loop2 = sorted(
        (loop1, loop2),
        key=lambda l: min(
            abs(p.position().x())
            for p in l
        ),
    )
    return loop1, loop2
