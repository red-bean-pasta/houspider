import math

import hou
from houkit.topology import fill_face, points_to_positions

from ..helper import bridge_loops
from .helper import loop_cut_tube


def fill_membranes(
    geo: hou.Geometry,
    thickness_pts: list[hou.Point],
) -> list[hou.Point]:
    """Create the middle loops bridging segment inset thickness loops across each joint.

    Returns mid_pts with 4 points per joint ordered [lb, rb, ru, lu].
    """
    if not thickness_pts:
        return []

    assert len(thickness_pts) % 8 == 0, f"Expected thickness_pts length to be a multiple of 8, got {len(thickness_pts)}"

    membrane_points: list[hou.Point] = []
    num_joints = len(thickness_pts) // 8
    for i in range(num_joints):
        former_end = thickness_pts[i * 8:i * 8 + 4]
        latter_start = thickness_pts[i * 8 + 4:(i + 1) * 8]
        membrane_points.extend(_add_membrane_joint(geo, former_end, latter_start))

    return membrane_points


def add_membrane_loop_cuts(
    geo: hou.Geometry,
    cube_pts: list[hou.Point],
    thickness_pts: list[hou.Point],
    mem_pts: list[hou.Point],
    support_loop_ratio: float,
) -> list[hou.Point]:
    """Add support loop cuts near former and latter boundaries of each joint membrane.

    Returns all_mem_pts containing up to 12 points per joint (3 loops of 4 points):
      - 4 points: former support loop (loop index 1)
      - 4 points: middle loop (loop index 2)
      - 4 points: latter support loop (loop index 3)
    All loops preserve corner ordering [lb, rb, ru, lu].
    """
    assert len(thickness_pts) % 8 == 0, f"Expected thickness_pts length to be a multiple of 8, got {len(thickness_pts)}"
    coxa_width = cube_pts[0].position().distanceTo(cube_pts[1].position())
    cut_length = coxa_width * support_loop_ratio

    num_joints = len(thickness_pts) // 8
    all_mem_pts: list[hou.Point] = []

    for i in range(num_joints):
        former_end = thickness_pts[i * 8:i * 8 + 4]
        latter_start = thickness_pts[i * 8 + 4:(i + 1) * 8]
        mid_pts = mem_pts[i * 4:(i + 1) * 4]

        # Use distance between upper corners to determine if cuts fit
        fu_corner = former_end[2]
        lu_corner = latter_start[2]
        half_width = fu_corner.position().distanceTo(lu_corner.position()) * 0.5
        if cut_length >= half_width:
            all_mem_pts.extend(mid_pts)
            continue

        former_cut = loop_cut_tube(geo, former_end, mid_pts, cut_length)
        latter_cut = loop_cut_tube(geo, latter_start, mid_pts, cut_length)
        all_mem_pts.extend([
            *former_cut,
            *mid_pts,
            *latter_cut,
        ])

    return all_mem_pts


def close_tarsus(
    geo: hou.Geometry,
    seg_pts: list[hou.Point],
    tarsus_wedge_angle: float,
) -> None:
    """Cap the end of the tarsus segment with an outward-facing quad and apply wedging to bottom corners."""
    assert len(seg_pts) >= 4, f"Expected at least 4 seg_pts, got {len(seg_pts)}"
    # Last loop of tarsus ordered [lb, rb, ru, lu]
    p_lb, p_rb, p_ru, p_lu = seg_pts[-4:]

    # [lb, rb, ru, lu] winding normal points along -Z (out of tarsus tip)
    fill_face([p_lb, p_rb, p_ru, p_lu])

    pos_lb, pos_rb, pos_ru, pos_lu = points_to_positions([p_lb, p_rb, p_ru, p_lu])
    offset_y = pos_lu.y() - pos_lb.y()
    offset_z = offset_y * math.tan(math.radians(tarsus_wedge_angle))

    # Apply wedge offset to bottom corners
    p_lb.setPosition(hou.Vector3(pos_lb.x(), pos_lb.y(), pos_lb.z() - offset_z))
    p_rb.setPosition(hou.Vector3(pos_rb.x(), pos_rb.y(), pos_rb.z() - offset_z))


def _add_membrane_joint(
    geo: hou.Geometry,
    former_end: list[hou.Point],
    latter_start: list[hou.Point],
) -> list[hou.Point]:
    """Create a middle loop between former and latter segment insets and bridge the quads."""
    midpoint_positions = _get_membrane_joint_midpoint_positions(former_end, latter_start)
    mid_loop = list(_create_membrane_midpoints(geo, midpoint_positions))

    bridge_loops(geo, former_end, mid_loop)
    bridge_loops(geo, mid_loop, latter_start)
    return mid_loop


def _get_membrane_joint_midpoint_positions(
    former_end: list[hou.Point],
    latter_start: list[hou.Point],
) -> tuple[hou.Vector3, hou.Vector3, hou.Vector3, hou.Vector3]:
    """Calculate positions for middle loop points ordered [lb, rb, ru, lu]."""
    # former_end and latter_start are ordered [lb, rb, ru, lu]
    (
        pos_fb1,
        pos_fb2,
        pos_fu2,
        pos_fu1,
        pos_lb1,
        pos_lb2,
        pos_lu2,
        pos_lu1,
    ) = points_to_positions(former_end + latter_start)

    lf = pos_fu1.distanceTo(pos_fb1)
    ll = pos_lu1.distanceTo(pos_lb1)
    membrane_length = (lf + ll) * 0.5

    pos_mb1 = (pos_fb1 + pos_lb1) * 0.5
    pos_mb2 = (pos_fb2 + pos_lb2) * 0.5
    pos_mu2 = (pos_fu2 + pos_lu2) * 0.5
    pos_mu1 = (pos_fu1 + pos_lu1) * 0.5
    pos_mb1[1] = (pos_mb1.y() + (pos_mu1.y() - membrane_length)) * 0.5
    pos_mb2[1] = (pos_mb2.y() + (pos_mu2.y() - membrane_length)) * 0.5

    # Return in order: 0: lb, 1: rb, 2: ru, 3: lu
    return pos_mb1, pos_mb2, pos_mu2, pos_mu1


def _create_membrane_midpoints(
    geo: hou.Geometry,
    positions: tuple[hou.Vector3, hou.Vector3, hou.Vector3, hou.Vector3],
) -> tuple[hou.Point, hou.Point, hou.Point, hou.Point]:
    points = [geo.createPoint() for _ in positions]
    for point, position in zip(points, positions):
        point.setPosition(position)
    return tuple(points)
