from collections.abc import Collection

import hou
from houkit.attributer import points_start_with

from .selector import get_pedipalp_socket_points, get_coxa_socket_points, get_local_z_value, get_local_z_direction, \
    traverse_limb_prims, group_membrane_rings
from ..abdomens.attributes import abdomenend
from ..attributes import GlobalAttrib
from ..bases.attributes import basecoxamemebrane
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
    socket_pts = get_coxa_socket_points(geo, is_right, leg_index)
    assert len(socket_pts) == 4, f"Expected 4 socket points for leg {'R' if is_right else 'L'}{leg_index}, got {len(socket_pts)}"
    return _extract_limb_bone_positions(socket_pts, spine_ratio)


def get_pedipalp_bone_positions(
    geo: hou.Geometry,
    is_right: bool,
) -> list[hou.Vector3]:
    spine_ratio = geo.attribValue(SPINE_RATIO)
    socket_pts = get_pedipalp_socket_points(geo, is_right)
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

    prims, pts = traverse_limb_prims(socket_pts)
    membranes = group_membrane_rings(prims)

    first_membrane = membranes[0]
    direction = get_local_z_direction(first_membrane[1])

    membrane_spines = [
        _calculate_spine_position(_get_former_segment_end_points(group[1], direction), spine_ratio)
        for group in membranes
    ]
    tip_pos = _find_tip_position(pts, direction, spine_ratio)

    return [socket_spine, *membrane_spines, tip_pos]


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
    return sorted(boundaries, key=lambda p: get_local_z_value(p, direction))[:4]


def _find_tip_position(
    limb_points: set[hou.Point],
    direction: hou.Vector3,
    spine_ratio: float,
) -> hou.Vector3:
    furthest_points = sorted(limb_points, key=lambda p: get_local_z_value(p, direction))[-4:]
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
