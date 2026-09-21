from collections.abc import Collection

import hou
from houkit.attributer import points_start_with
from houkit.topology import is_neighbor

from ..abdomens.attributes import abdomenend
from ..attributes import GlobalAttrib
from ..bases.attributes import basecoxamemebrane, basemaxillamembrane
from ..helper import positions_from_geo
from ..legs.attributes import Region
from ..spiders.attributes import ID as PEDICEL_IDS


SPINE_RATIO = GlobalAttrib.SPINE_RATIO


def get_body_bone_positions(geo: hou.Geometry) -> list[hou.Vector3]:
    root_pos = get_root_position(geo)
    pedicel_pos = _get_averaged_position(geo, tuple(PEDICEL_IDS))
    abdomen_pos, = positions_from_geo(geo, abdomenend())
    return [root_pos, pedicel_pos, abdomen_pos]


def get_leg_bone_positions(
    geo: hou.Geometry,
    is_right: bool,
    leg_index: int,
) -> list[hou.Vector3]:
    spine_ratio = geo.attribValue(SPINE_RATIO)

    leg_affix = leg_index if is_right else -leg_index
    prefix = f"{basecoxamemebrane(leg_affix)}_"
    socket_pts = points_start_with(geo, "id", prefix)
    assert len(socket_pts) == 4, f"Expected 4 socket points for {prefix}, got {len(socket_pts)}"
    return _extract_limb_bone_positions(socket_pts, spine_ratio)


def get_pedipalp_bone_positions(
    geo: hou.Geometry,
    is_right: bool,
) -> list[hou.Vector3]:
    spine_ratio = geo.attribValue(SPINE_RATIO)

    left_socket_pts = points_start_with(geo, "id", basemaxillamembrane("-"))
    if is_right:
        socket_pts = [
            p
            for p in points_start_with(geo, "id", basemaxillamembrane())
            if p not in left_socket_pts
        ]
    else:
        socket_pts = left_socket_pts

    assert len(socket_pts) == 4, f"Expected 4 socket points for pedipalp {'R' if is_right else 'L'}, got {len(socket_pts)}"
    return _extract_limb_bone_positions(socket_pts, spine_ratio)


def get_root_position(geo: hou.Geometry) -> hou.Vector3:
    pts = points_start_with(geo, "id", basecoxamemebrane())
    assert pts, "Expected coxa socket points on geometry"
    avg = sum((p.position() for p in pts), hou.Vector3()) / len(pts)
    return hou.Vector3(0.0, avg.y(), avg.z())


def _extract_limb_bone_positions(
    socket_pts: list[hou.Point],
    spine_ratio: float,
) -> list[hou.Vector3]:
    socket_spine = _calculate_spine_position(socket_pts, spine_ratio)

    prims, pts = _traverse_limb_prims(socket_pts)
    membranes = _group_membrane_rings(prims)

    first_membrane = min(membranes, key=lambda m: sum(p.position().length() for p in m[1]) / len(m[1]))
    direction = _get_local_z_direction(first_membrane[1])

    sorted_rings = sorted(
        [r[1] for r in membranes],
        key=lambda ring: sum(_get_local_z_value(p, direction) for p in ring) / len(ring),
    )

    membrane_spines = [
        _calculate_spine_position(_get_former_segment_end_points(group, direction), spine_ratio)
        for group in sorted_rings
    ]
    tip_pos = _find_tip_position(pts, direction, spine_ratio)

    return [socket_spine, *membrane_spines, tip_pos]


def _get_local_z_direction(
    membrane_points: Collection[hou.Point],
) -> hou.Vector3:
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

    m1 = sum((p.position() for p in loop1), hou.Vector3()) / 4.0
    m2 = sum((p.position() for p in loop2), hou.Vector3()) / 4.0
    former, latter = (m1, m2) if m1.length() < m2.length() else (m2, m1)
    direction = (latter - former).normalized()
    return hou.Vector3(direction.x(), 0.0, direction.z()).normalized()


def _get_local_z_value(
    target: hou.Point | hou.Vector3,
    direction: hou.Vector3,
) -> float:
    pos = target.position() if isinstance(target, hou.Point) else target
    return pos.dot(direction)


def _get_former_segment_end_points(
    membrane_points: Collection[hou.Point],
    direction: hou.Vector3,
) -> list[hou.Point]:
    boundaries = [
        p
        for p in membrane_points
        if any(pr.stringAttribValue("region") == Region.LEGSEGMENT for pr in p.prims())
    ]
    assert len(boundaries) == 8, f"Expected 8 boundary points on membrane ring, got {len(boundaries)}"
    return sorted(boundaries, key=lambda p: _get_local_z_value(p, direction))[:4]


def _find_tip_position(
    limb_points: set[hou.Point],
    direction: hou.Vector3,
    spine_ratio: float,
) -> hou.Vector3:
    furthest_points = sorted(limb_points, key=lambda p: _get_local_z_value(p, direction))[-4:]
    return _calculate_spine_position(furthest_points, spine_ratio)


def _calculate_spine_position(
    points: Collection[hou.Point],
    spine_ratio: float,
) -> hou.Vector3:
    assert len(points) == 4, f"Expected 4 points for cross-section spine calculation, got {len(points)}"
    sorted_by_y = sorted(points, key=lambda p: p.position().y())
    btm1, btm2 = sorted_by_y[0], sorted_by_y[1]
    top1, top2 = sorted_by_y[2], sorted_by_y[3]
    mid_top = (top1.position() + top2.position()) * 0.5
    mid_btm = (btm1.position() + btm2.position()) * 0.5
    return mid_top * (1.0 - spine_ratio) + mid_btm * spine_ratio


def _traverse_limb_prims(
    socket_pts: list[hou.Point],
) -> tuple[set[hou.Prim], set[hou.Point]]:
    visited_prims: set[hou.Prim] = set()
    visited_pts: set[hou.Point] = set(socket_pts)

    queue: list[hou.Point] = list(socket_pts)
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


def _group_membrane_rings(
    prims: set[hou.Prim],
) -> list[tuple[set[hou.Prim], set[hou.Point]]]:
    mem_prims = [p for p in prims if p.stringAttribValue("region") == Region.LEGMEMBRANE]

    rings: list[tuple[set[hou.Prim], set[hou.Point]]] = []
    visited_mems: set[hou.Prim] = set()
    for prim in mem_prims:
        if prim in visited_mems:
            continue
        queue = [prim]
        comp_prims: set[hou.Prim] = set()
        visited_mems.add(prim)
        while queue:
            cur = queue.pop()
            comp_prims.add(cur)
            for pt in cur.points():
                for nbr in pt.prims():
                    if nbr in mem_prims and nbr not in visited_mems:
                        visited_mems.add(nbr)
                        queue.append(nbr)
        ring_pts = set({pt for p in comp_prims for pt in p.points()})
        rings.append((comp_prims, ring_pts))

    return rings


def _get_averaged_position(
    geo: hou.Geometry,
    starts_with: str | tuple[str],
    assert_found: bool = True
) -> hou.Vector3:
    poses = [
        p.position()
        for p in
        points_start_with(geo, "id", starts_with)
    ]
    if not poses:
        if assert_found:
            raise AssertionError(f"Expected points start with {starts_with} on geometry")
        return None
    return sum(poses, hou.Vector3()) / len(poses)
