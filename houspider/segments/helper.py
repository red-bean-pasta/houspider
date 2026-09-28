from hou import Geometry, Point, Vector3
from houkit.topology import loop_cut, points_to_positions

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
    cut_length: float,
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
        cut_length,
        use_ratio=False,
    )
    cut_pts = points_from_loop_cut(cut_edges)
    assert len(cut_pts) == 4, f"Expected four points from tube loop cut, got {len(cut_pts)}"
    return cut_pts
