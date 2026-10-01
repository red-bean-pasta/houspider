import math

from hou import Geometry, Point, Vector3
from houkit.models import Moject
from houkit.topologies.basic import fill_face, points_to_positions

from .cube import get_cube_points
from .helper import inset_loop, loop_cut_tube
from .models import LimbParam
from ..helper import bridge_loops


def build_segment_tubes(
    geo: Geometry,
    param: LimbParam,
) -> Moject[list[list[Point]]]:
    """Build the basic tubes for all segments of a leg.

    Each segment consists of 4-point loops (at least 8 points: 4 for start and 4 for end).
    Every 4-point loop in the leg strictly follows corner ordering:
      Index 0 (corner 1): Left Bottom  (-X, -Y)
      Index 1 (corner 2): Right Bottom (+X, -Y)
      Index 2 (corner 3): Right Upper  (+X, +Y)
      Index 3 (corner 4): Left Upper   (-X, +Y)
    """
    segments, messages = get_cube_points(param)

    segment_tubes: list[list[Point]] = []
    for seg in segments:
        cur_seg_pts = [geo.createPoint() for _ in range(len(seg))]
        for pt, pos in zip(cur_seg_pts, seg):
            pt.setPosition(pos)
        segment_tubes.append(cur_seg_pts)

        # Loop points are ordered [lb, rb, ru, lu], winding clockwise looking into the tube,
        # so bridge_loops automatically produces outward-facing surface normals.
        num_loops = len(cur_seg_pts) // 4
        for l in range(num_loops - 1):
            start_loop = cur_seg_pts[l * 4 : (l + 1) * 4]
            end_loop = cur_seg_pts[(l + 1) * 4 : (l + 2) * 4]
            bridge_loops(geo, start_loop, end_loop)

    return Moject(segment_tubes, messages)


def inset_segment_thickness(
    geo: Geometry,
    segment_tubes: list[list[Point]],
    support_loop_ratio: float,
) -> list[Point]:
    """Create inset thickness loops at segment ends and starts facing joint membranes.

    Returns thickness_pts where each joint has 8 points:
      - 4 points for former segment end inset (loop index 6)
      - 4 points for latter segment start inset (loop index 1)
    All loops preserve corner ordering [lb, rb, ru, lu].
    """
    coxa_width = segment_tubes[0][0].position().distanceTo(segment_tubes[0][1].position())
    cut_length = coxa_width * support_loop_ratio

    num_segs = len(segment_tubes)
    thickness_pts: list[Point] = []

    for i in range(num_segs - 1):
        former_end = segment_tubes[i][-4:]
        latter_start = segment_tubes[i + 1][:4]
        former_inset, latter_inset = _add_segment_thickness_loops(
            geo,
            former_end,
            latter_start,
            cut_length,
        )
        thickness_pts.extend([*former_inset, *latter_inset])

    return thickness_pts


def add_segment_loop_cuts(
    geo: Geometry,
    segment_tubes: list[list[Point]],
    support_loop_ratio: float,
) -> list[list[Point]]:
    """Add support loop cuts near the start and end of each segment tube.

    Returns seg_tubes containing loops per segment:
      - 4 points: start loop (edge 1)
      - 4 points: start support loop (support 1)
      - intermediate section loops (if any, ordered along segment)
      - 4 points: end support loop (support -1)
      - 4 points: end loop (edge -1)
    All loops preserve corner ordering [lb, rb, ru, lu].
    """
    coxa_width = segment_tubes[0][0].position().distanceTo(segment_tubes[0][1].position())
    cut_length = coxa_width * support_loop_ratio

    all_seg_tubes: list[list[Point]] = []

    for cur_pts in segment_tubes:
        start_pts = cur_pts[:4]
        end_pts = cur_pts[-4:]

        second_loop = cur_pts[4:8]
        penultimate_loop = cur_pts[-8:-4]
        start_cut = loop_cut_tube(geo, start_pts, second_loop, cut_length)
        cut_source = start_cut if len(cur_pts) == 8 else penultimate_loop
        end_cut = loop_cut_tube(geo, end_pts, cut_source, cut_length)
        all_seg_tubes.append([
            *start_pts,
            *start_cut,
            *cur_pts[4:-4],
            *end_cut,
            *end_pts,
        ])

    return all_seg_tubes


def close_tarsus(
    tarsus_pts: list[Point],
    tarsus_wedge_angle: float,
) -> None:
    """Cap the end of the tarsus segment with an outward-facing quad and apply wedging to bottom corners."""
    assert len(tarsus_pts) >= 4, f"Expected at least 4 tarsus_pts, got {len(tarsus_pts)}"
    # Last loop of tarsus ordered [lb, rb, ru, lu]
    p_lb, p_rb, p_ru, p_lu = tarsus_pts[-4:]

    # [lb, rb, ru, lu] winding normal points along -Z (out of tarsus tip)
    fill_face([p_lb, p_rb, p_ru, p_lu])

    pos_lb, pos_rb, pos_ru, pos_lu = points_to_positions([p_lb, p_rb, p_ru, p_lu])
    offset_y = pos_lu.y() - pos_lb.y()
    offset_z = offset_y * math.tan(math.radians(tarsus_wedge_angle))

    # Apply wedge offset to bottom corners
    p_lb.setPosition(Vector3(pos_lb.x(), pos_lb.y(), pos_lb.z() - offset_z))
    p_rb.setPosition(Vector3(pos_rb.x(), pos_rb.y(), pos_rb.z() - offset_z))


def _add_segment_thickness_loops(
    geo: Geometry,
    former_end: list[Point],
    latter_start: list[Point],
    cut_length: float,
) -> tuple[list[Point], list[Point]]:
    former_inset = inset_loop(geo, former_end, cut_length)
    latter_inset = inset_loop(geo, latter_start, cut_length)

    # Former end faces outward along -Z into the joint (reverse=False gives [0, 0, -1] normal)
    bridge_loops(
        geo,
        former_end,
        former_inset,
        reverse=False,
    )

    # Latter start faces outward along +Z into the joint (reverse=True gives [0, 0, 1] normal)
    bridge_loops(
        geo,
        latter_start,
        latter_inset,
        reverse=True,
    )
    return former_inset, latter_inset
