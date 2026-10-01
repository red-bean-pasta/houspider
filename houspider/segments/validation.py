import hou


def validate_segment_loops(
    seg_pts: list[hou.Point],
    points_per_loop: int = 4,
    points_per_seg: int = 16,
) -> list[str]:
    """Validate that segment loops stay ordered within boundaries and do not invert."""
    assert len(seg_pts) % points_per_seg == 0, (
        f"Expected seg_pts length to be a multiple of {points_per_seg}, got {len(seg_pts)}"
    )

    num_segs = len(seg_pts) // points_per_seg
    warnings: list[str] = []

    for seg_idx in range(num_segs):
        cur_pts = seg_pts[seg_idx * points_per_seg : (seg_idx + 1) * points_per_seg]
        warning = _validate_segment(cur_pts, seg_idx + 1, points_per_loop)
        if warning:
            warnings.append(warning)

    return warnings


def _validate_segment(
    seg_pts: list[hou.Point],
    seg_num: int,
    points_per_loop: int,
) -> str | None:
    loops = [seg_pts[i : i + points_per_loop] for i in range(0, len(seg_pts), points_per_loop)]
    start_positions = [pt.position() for pt in loops[0]]
    end_positions = [pt.position() for pt in loops[-1]]

    c_start = sum(start_positions, hou.Vector3()) / len(start_positions)
    c_end = sum(end_positions, hou.Vector3()) / len(end_positions)
    axis = c_end - c_start
    if axis.length() < 1e-6:
        return f"Segment {seg_num}: collapsed segment axis."
    u = axis.normalized()

    for corner_idx in range(points_per_loop):
        s_start = (start_positions[corner_idx] - c_start).dot(u)
        s_end = (end_positions[corner_idx] - c_start).dot(u)

        if s_end <= s_start:
            return f"Segment {seg_num}: corner edge collapsed or inverted."

        prev_s = s_start
        for mid_loop in loops[1:-1]:
            s_mid = (mid_loop[corner_idx].position() - c_start).dot(u)
            if s_mid < s_start or s_mid > s_end or s_mid < prev_s:
                return f"Segment {seg_num}: middle loop cuts exceed boundary or inverted."
            prev_s = s_mid

    return None
