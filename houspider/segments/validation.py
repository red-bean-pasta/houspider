import hou


CORNER_NAMES = ("left bottom", "right bottom", "right upper", "left upper")


def validate_segment_loops(
    seg_pts: list[hou.Point],
    points_per_loop: int = 4,
    points_per_seg: int = 16,
) -> list[str]:
    """Validate that middle section loops stay within start and end sections, and corners do not invert."""
    assert len(seg_pts) % points_per_seg == 0, (
        f"Expected seg_pts length to be a multiple of {points_per_seg}, got {len(seg_pts)}"
    )

    num_segs = len(seg_pts) // points_per_seg
    warnings: list[str] = []

    for seg_idx in range(num_segs):
        cur_pts = seg_pts[seg_idx * points_per_seg : (seg_idx + 1) * points_per_seg]
        seg_warnings = _validate_single_segment(cur_pts, seg_idx + 1, points_per_loop)
        warnings.extend(seg_warnings)

    return warnings


def _validate_single_segment(
    seg_pts: list[hou.Point],
    seg_num: int,
    points_per_loop: int,
) -> list[str]:
    loops = [seg_pts[i : i + points_per_loop] for i in range(0, len(seg_pts), points_per_loop)]
    start_loop = loops[0]
    end_loop = loops[-1]
    middle_loops = loops[1:-1]

    start_positions = [pt.position() for pt in start_loop]
    end_positions = [pt.position() for pt in end_loop]

    c_start = sum(start_positions, hou.Vector3()) / len(start_positions)
    c_end = sum(end_positions, hou.Vector3()) / len(end_positions)
    axis = c_end - c_start
    axis_len = axis.length()
    if axis_len < 1e-6:
        return [f"Segment {seg_num}: collapsed segment axis (length {axis_len:.4f})."]

    u = axis / axis_len
    warnings: list[str] = []

    for corner_idx in range(points_per_loop):
        corner_name = CORNER_NAMES[corner_idx] if corner_idx < len(CORNER_NAMES) else f"corner {corner_idx + 1}"
        s_start = (start_positions[corner_idx] - c_start).dot(u)
        s_end = (end_positions[corner_idx] - c_start).dot(u)

        if s_end <= s_start:
            warnings.append(
                f"Segment {seg_num} ({corner_name}): edge inverted/collapsed along segment axis "
                f"(start section at {s_start:.3f}, end section at {s_end:.3f})."
            )
            continue

        prev_s = s_start
        for loop_idx, mid_loop in enumerate(middle_loops, start=1):
            s_mid = (mid_loop[corner_idx].position() - c_start).dot(u)
            if s_mid < s_start:
                warnings.append(
                    f"Segment {seg_num} loop {loop_idx} ({corner_name}): exceeds start section along axis "
                    f"({s_mid:.3f} < {s_start:.3f})."
                )
            elif s_mid > s_end:
                warnings.append(
                    f"Segment {seg_num} loop {loop_idx} ({corner_name}): exceeds end section along axis "
                    f"({s_mid:.3f} > {s_end:.3f})."
                )
            elif s_mid < prev_s:
                warnings.append(
                    f"Segment {seg_num} loops {loop_idx - 1} and {loop_idx} ({corner_name}): inverted/crossed along axis "
                    f"({prev_s:.3f} > {s_mid:.3f})."
                )
            prev_s = s_mid

    return warnings
