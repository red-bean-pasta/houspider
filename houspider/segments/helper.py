from hou import Geometry, Point, Vector3
from houkit.topology import loop_cut, offset_point, points_to_positions

from ..helper import points_from_loop_cut


def inset_loop(
    geo: Geometry,
    pts: list[Point],
    cut_length: float,
) -> list[Point]:
    """Inset a 4-point loop towards its center, preserving [lb, rb, ru, lu] ordering."""
    assert len(pts) == 4
    pos_lb, pos_rb, pos_ru, pos_lu = points_to_positions(pts)
    v_up = pos_ru - pos_rb
    width = pos_rb.x() - pos_lb.x()
    height = v_up.length()
    if width <= 1e-6 or height <= 1e-6 or cut_length <= 0:
        raise ValueError("Inset loop requires positive width, height, and cut length")
    cut_length = min(cut_length, 0.49 * min(width, height))
    dir_up = v_up.normalized()

    pos_in_lb = pos_lb + Vector3(cut_length, 0, 0) + dir_up * cut_length
    pos_in_rb = pos_rb + Vector3(-cut_length, 0, 0) + dir_up * cut_length
    pos_in_ru = pos_ru + Vector3(-cut_length, 0, 0) - dir_up * cut_length
    pos_in_lu = pos_lu + Vector3(cut_length, 0, 0) - dir_up * cut_length

    p_in = [geo.createPoint() for _ in range(4)]
    for p, pos in zip(p_in, (pos_in_lb, pos_in_rb, pos_in_ru, pos_in_lu)):
        p.setPosition(pos)
    return p_in


def loop_cut_tube(
    geo: Geometry,
    start_pts: list[Point],
    end_pts: list[Point],
    cut_ratio: float,
) -> list[Point]:
    """Add a loop cut across a 4-sided tube and return the 4 cut points ordered [lb, rb, ru, lu]."""
    s0, s1, s2, s3 = start_pts
    e0, e1, e2, e3 = end_pts

    edge = geo.findEdge(s0, e0)
    assert edge is not None, f"Expected edge between {s0} and {e0}"
    prim = [p for p in edge.prims() if s1 in p.points()][0]
    cut_edges = loop_cut(
        prim,
        s0,
        e0,
        cut_ratio,
        use_ratio=True,
    )
    cut_pts = points_from_loop_cut(cut_edges)
    assert len(cut_pts) == 4, f"Expected four points from tube loop cut, got {len(cut_pts)}"
    return cut_pts


def compute_intermediate_ratios(
    segment: list[Point] | list[Vector3],
) -> list[float]:
    start_pts = segment[:4]
    end_pts = segment[-4:]
    ratios: list[float] = []
    for offset, pt in enumerate(segment[4:-4]):
        corner = offset % 4
        p_start = _position(start_pts[corner])
        p_end = _position(end_pts[corner])
        p = _position(pt)
        v_edge = p_end - p_start
        len_sq = v_edge.lengthSquared()
        t = (p - p_start).dot(v_edge) / len_sq if len_sq > 1e-10 else 0.0
        ratios.append(t)
    return ratios


def update_intermediate_positions(
    segment: list[Point] | list[Vector3],
    ratios: list[float],
) -> None:
    """Follow the captured ratios along local Z, preserving section width and height."""
    local_z = (_position(segment[0]) - _position(segment[-4])).normalized()
    start_pts = segment[:4]
    end_pts = segment[-4:]
    for offset, t in enumerate(ratios):
        corner = offset % 4
        target = _position(start_pts[corner]) * (1.0 - t) + _position(end_pts[corner]) * t
        idx = 4 + offset
        displacement = local_z * (target - _position(segment[idx])).dot(local_z)
        if isinstance(segment[idx], Point):
            offset_point(segment[idx], displacement)
        else:
            segment[idx] += displacement


def _position(point: Point | Vector3) -> Vector3:
    return point.position() if isinstance(point, Point) else point
