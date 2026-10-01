import hou
from houkit.topology import points_to_positions

from .helper import loop_cut_tube
from ..helper import bridge_loops


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
    cube_pts: list[hou.Point] | list[list[hou.Point]],
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
    first_loop = cube_pts[0] if isinstance(cube_pts[0], list) else cube_pts
    coxa_width = first_loop[0].position().distanceTo(first_loop[1].position())
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
