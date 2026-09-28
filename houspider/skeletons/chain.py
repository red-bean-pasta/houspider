import hou
from houkit.attributer import points_start_with

from ..abdomens.attributes import abdomenend
from ..bases.attributes import basecoxamemebrane, basemaxillamembrane
from ..helper import points_from_geo, positions_from_geo
from ..legs.attributes import legsegment
from ..pedipalps.attributes import pedipalpsegment
from ..spiders.attributes import ID as PEDICEL_IDS


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
    affix_idx = leg_index if is_right else -leg_index

    # 1. Socket hinge: midpoint of top corners (ru, lu) of coxa socket
    s3, s4 = points_from_geo(geo, basecoxamemebrane(affix_idx, 3), basecoxamemebrane(affix_idx, 4))
    socket_hinge = (s3.position() + s4.position()) * 0.5

    # 2. Joint hinges 1..6: midpoint of top corners (ru, lu) of former segment end inset (loop 6)
    joint_hinges = [
        _midpoint_from_ids(
            geo,
            legsegment(affix_idx, k, 6, 3),
            legsegment(affix_idx, k, 6, 4),
        )
        for k in range(1, 7)
    ]

    # 3. Tip hinge: midpoint of top corners (ru, lu) of tarsus end (seg 7, loop 5)
    tip_hinge = _midpoint_from_ids(
        geo,
        legsegment(affix_idx, 7, 5, 3),
        legsegment(affix_idx, 7, 5, 4),
    )

    return [socket_hinge, *joint_hinges, tip_hinge]


def get_pedipalp_bone_positions(
    geo: hou.Geometry,
    is_right: bool,
) -> list[hou.Vector3]:
    side = 1 if is_right else -1

    # 1. Socket hinge: midpoint of the two highest socket points
    left_pts = points_start_with(geo, "id", basemaxillamembrane("-"))
    socket_pts = [p for p in points_start_with(geo, "id", basemaxillamembrane()) if p not in left_pts] if is_right else left_pts
    assert len(socket_pts) == 4, f"Expected 4 socket points for pedipalp {'R' if is_right else 'L'}, got {len(socket_pts)}"
    sorted_by_y = sorted(socket_pts, key=lambda p: p.position().y())
    socket_hinge = (sorted_by_y[2].position() + sorted_by_y[3].position()) * 0.5

    # 2. Joint hinges 1..5: midpoint of top corners (ru, lu) of former segment end inset (loop 6)
    joint_hinges = [
        _midpoint_from_ids(
            geo,
            pedipalpsegment(side, k, 6, 3),
            pedipalpsegment(side, k, 6, 4),
        )
        for k in range(1, 6)
    ]

    # 3. Tip hinge: midpoint of top corners (ru, lu) of tarsus end (seg 6, loop 5)
    tip_hinge = _midpoint_from_ids(
        geo,
        pedipalpsegment(side, 6, 5, 3),
        pedipalpsegment(side, 6, 5, 4),
    )

    return [socket_hinge, *joint_hinges, tip_hinge]


def get_root_position(geo: hou.Geometry) -> hou.Vector3:
    pts = points_start_with(geo, "id", basecoxamemebrane())
    assert pts, "Expected coxa socket points on geometry"
    avg = sum((p.position() for p in pts), hou.Vector3()) / len(pts)
    return hou.Vector3(0.0, avg.y(), avg.z())


def _midpoint_from_ids(
    geo: hou.Geometry,
    id_a: str,
    id_b: str,
) -> hou.Vector3:
    p_a, p_b = points_from_geo(geo, id_a, id_b)
    return (p_a.position() + p_b.position()) * 0.5


def _get_averaged_position(
    geo: hou.Geometry,
    starts_with: str | tuple[str],
    assert_found: bool = True,
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
