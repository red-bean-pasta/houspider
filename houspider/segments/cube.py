import math

from hou import Vector3, Vector2
from houkit.models import Moject

from .models import LimbParam


def get_cube_points(
    param: LimbParam,
) -> Moject[list[list[Vector3]]]:
    assert len(param.yaw_flex_specs) == len(param.length_ratios)

    coxa = _build_segment(param.socket_size, param.segment_sections[0], param.coxa_length)

    messages: list[str] = []
    segments: list[list[Vector3]] = [coxa]
    for i, (max_yaw, min_flex) in enumerate(param.yaw_flex_specs):
        cur_sections = param.segment_sections[i + 1]
        seg_length = param.coxa_length * param.length_ratios[i]
        former = segments[-1]
        former_end_w, former_end_h = _get_section_width_height(former, -1)
        latter = _build_segment((former_end_w, former_end_h), cur_sections, seg_length)
        latter_start_w, latter_start_h = _get_section_width_height(latter, 0)

        (offset, wedge_angle), seg_messages = _calc_segment_offset_and_wedge(
            max_yaw,
            min_flex,
            param.spine_ratio,
            ((former_end_w, former_end_h), (latter_start_w, latter_start_h)),
            param.minimum_membrane,
        )
        messages.extend(seg_messages)

        _position_latter_segment(former, latter, offset)
        _wedge_joint(former, latter, wedge_angle)
        segments.append(latter)

    assert len(segments) == len(param.yaw_flex_specs) + 1
    return Moject(segments, messages)


def _build_segment(
    reference_section: tuple[float, float],
    sections: tuple[tuple[float, float, float], ...],
    length: float,
) -> list[Vector3]:
    ref_w, ref_h = reference_section
    points: list[Vector3] = []
    for len_ratio, w_ratio, h_ratio in sections:
        w = ref_w * w_ratio
        h = ref_h * h_ratio
        hw = w / 2.0
        hh = h / 2.0
        z = -length * len_ratio
        # Loop corners ordered: 0: left bottom, 1: right bottom, 2: right upper, 3: left upper
        points.extend([
            Vector3(-hw, -hh, z),
            Vector3(hw, -hh, z),
            Vector3(hw, hh, z),
            Vector3(-hw, hh, z),
        ])
    return points


def _position_latter_segment(
    former: list[Vector3],
    latter: list[Vector3],
    offset: Vector2,
) -> None:
    former_end = former[-4:]
    former_end_center = sum(former_end, Vector3()) / len(former_end)
    _, former_end_h = _get_section_width_height(former, -1)
    _, latter_start_h = _get_section_width_height(latter, 0)
    target_center = Vector3(
        0.0,
        former_end_center.y() + (former_end_h - latter_start_h) / 2 + offset.y(),
        former_end_center.z() - offset.x(),
    )
    _offset_segment(latter, target_center)


def _offset_segment(
    positions: list[Vector3],
    offset: Vector3,
) -> list[Vector3]:
    for i in range(len(positions)):
        positions[i] = positions[i] + offset
    return positions


def _get_section_width_height(positions: list[Vector3], index: int) -> tuple[float, float]:
    start = index * 4 if index >= 0 else len(positions) + index * 4
    section = positions[start: start + 4]
    w = section[2].x() - section[3].x()
    h = section[2].y() - section[1].y()
    return w, h


def _wedge_joint(
    former_segment: list[Vector3],
    latter_segment: list[Vector3],
    wedge_angle: float,
) -> None:
    def _wedge_bottom(
        segment: list[Vector3],
        section_index: int,
        direction: float,
    ) -> None:
        _, height = _get_section_width_height(segment, section_index)
        delta = height * math.tan(math.radians(wedge_angle)) * direction
        start = section_index * 4 if section_index >= 0 else len(segment) + section_index * 4
        segment[start] += Vector3(0.0, 0.0, delta)
        segment[start + 1] += Vector3(0.0, 0.0, delta)

    _wedge_bottom(former_segment, -1, 1.0)
    _wedge_bottom(latter_segment, 0, -1.0)


def _calc_segment_offset_and_wedge(
    max_yaw: float,
    min_flex: float,
    spine_ratio: float,
    segment_size: tuple[tuple[float, float], tuple[float, float]],
    minimum_membrane: tuple[float, float],
) -> Moject[tuple[Vector2, float]]:
    (former_width, former_height), (latter_width, latter_height) = segment_size

    (offset_x, wedge_angle), messages = _calc_membrane_spec(max_yaw, min_flex, segment_size, minimum_membrane)

    # Keep the spine position (the point at spine_ratio from the top) aligned
    # across the joint, moving the latter segment in either vertical direction.
    offset_y = (latter_height - former_height) * spine_ratio

    wedged_x = abs(offset_y) * math.tan(math.radians(wedge_angle))
    offset_x -= wedged_x
    offset_x = max(offset_x, minimum_membrane[0])

    return Moject((Vector2(offset_x, offset_y), wedge_angle), messages)


def _calc_membrane_spec(
    max_yaw_deg: float,
    min_flex_deg: float,
    segment_sections: tuple[tuple[float, float], tuple[float, float]],
    min_return: tuple[float, float],
    max_wedge_deg: float = 45,
    max_distance_ratio: float = 1.0,
) -> Moject[tuple[float, float]]:
    max_yaw_deg = abs(max_yaw_deg)
    assert min_flex_deg > 0
    assert max_yaw_deg <= 90

    min_distance, min_angle = min_return
    assert min_distance > 0 and 0 < min_angle < 45

    messages: list[str] = []
    (former_width, former_height), (latter_width, latter_height) = segment_sections
    distance = latter_width / 2 * math.sin(math.radians(max_yaw_deg))
    distance = max(distance, min_distance)

    if min_flex_deg >= 180:
        angle = min_angle
        return Moject((distance, angle), messages)

    min_height = min(former_height, latter_height)
    angle, wedge_messages = _solve_membrane_wedge_deg(
        min_flex_deg,
        distance,
        min_height,
    )
    messages.extend(wedge_messages)
    angle = max(angle, min_return[1])
    limited_distance, limited_angle, limit_messages = _apply_membrane_spec_limits(
        distance,
        angle,
        min_distance,
        min_flex_deg,
        min_height,
        former_width,
        latter_width,
        max_wedge_deg,
        max_distance_ratio,
    )
    messages.extend(limit_messages)

    return Moject((limited_distance, limited_angle), messages)


def _apply_membrane_spec_limits(
    distance: float,
    angle: float,
    min_distance: float,
    min_flex_deg: float,
    min_height: float,
    former_width: float,
    latter_width: float,
    max_wedge_deg: float,
    max_distance_ratio: float,
) -> tuple[float, float, list[str]]:
    if angle <= max_wedge_deg:
        return distance, angle, []

    angle = max_wedge_deg
    distance = _solve_membrane_thickness_deg(
        180 - 2 * max_wedge_deg - min_flex_deg,
        min_height,
        max_wedge_deg,
    )
    messages: list[str] = []
    max_distance = max(former_width, latter_width) * max_distance_ratio
    if distance > max_distance:
        max_membrane_angle = math.degrees(
            math.atan(max_distance * math.cos(math.radians(max_wedge_deg)) / min_height)
        )
        min_flex_ceiling = 180 - 2 * max_wedge_deg - max_membrane_angle
        messages.append(
            f"Membrane distance ({distance:.4f}) exceeded max_distance_ratio limit "
            f"({max_distance:.4f}). Max angle ceiling reached with max_wedge_deg={max_wedge_deg}° "
            f"and max_distance_ratio={max_distance_ratio}, limiting min flex angle ceiling to {min_flex_ceiling:.2f}° "
            f"(requested {min_flex_deg:.2f}°)."
        )
        distance = max_distance
    distance = max(distance, min_distance)
    return distance, angle, messages


def _solve_membrane_wedge_deg(
    min_flex: float,
    membrane_thickness: float,
    min_height: float,
    tolerance: float = 1e-5,
    iterations: int = 50,
) -> Moject[float]:
    wedge_rad, messages = _solve_membrane_wedge_rad(
        math.radians(min_flex),
        membrane_thickness,
        min_height,
        tolerance,
        iterations,
    )
    return Moject(math.degrees(wedge_rad), messages)


def _solve_membrane_wedge_rad(
    min_flex: float,
    membrane_thickness: float,
    min_height: float,
    tolerance: float = 1e-5,
    iterations: int = 50,
) -> Moject[float]:
    remain_rad, messages = _solve_membrane_wedge_remain_rad(
        min_flex,
        membrane_thickness,
        min_height,
        tolerance,
        iterations,
    )
    return Moject(math.pi / 2 - remain_rad, messages)


def _solve_membrane_wedge_remain_rad(
    min_flex: float,
    membrane_thickness: float,
    min_height: float,
    tolerance: float = 1e-5,
    iterations: int = 50,
) -> Moject[float]:
    """
    :solve:
        u: pi / 2 - wedge_angle
        w: max rotate angle introduced by membrane thickness
        2u - w = min_flex
        tan(w) = d / (h / sin(u))
    :return: in radians
    """
    assert min_height > 0 and membrane_thickness > 0

    k = membrane_thickness / min_height

    u = min_flex * 0.5
    f = 0.0
    for _ in range(iterations):
        w = 2.0 * u - min_flex
        cos_w = math.cos(w)
        assert abs(cos_w) >= tolerance, "Solver reached tan(w) singularity"

        f = math.tan(w) - k * math.sin(u)
        if abs(f) < tolerance:
            return Moject(u)
        df = 2.0 / (cos_w * cos_w) - k * math.cos(u)
        assert abs(df) >= tolerance, "Derivative too small"
        u -= f / df

    msg = (
        f"Membrane wedge solver exhausted {iterations} iterations without converging to tolerance {tolerance:.2e} "
        f"(final residual: {abs(f):.4e}, min_flex: {math.degrees(min_flex):.2f}°, "
        f"membrane_thickness: {membrane_thickness:.4f}, min_height: {min_height:.4f})."
    )
    return Moject(u, [msg])


def _solve_membrane_thickness_deg(
    needed_angle: float,
    min_height: float,
    wedge_angle: float,
) -> float:
    return _solve_membrane_thickness_rad(
        math.radians(needed_angle),
        min_height,
        math.radians(wedge_angle),
    )


def _solve_membrane_thickness_rad(
    needed_angle: float,
    min_height: float,
    wedge_angle: float,
) -> float:
    """
    :param needed_angle: in radians
    :param min_height:
    :param wedge_angle: in radians
    :return:
    """
    # d / tan(needed_angle) = l = min_height / cos(wedge_angle)
    return min_height / math.cos(wedge_angle) * math.tan(needed_angle)
