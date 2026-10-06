import math

import hou
from houkit.noder import get_parent
from houkit.parameterizer import get_parms

from houspider.helper import add_id_point, get_control_parms, points_by_id, positions_from_geo, replace_points
from houspider.sternums.attributes import ID, sternumrimmiddle, sternumrim, sternumspine


def add_right_half(node: hou.SopNode) -> None:
    geo = node.geometry()
    parent = get_parent(node)

    params = get_parms(parent, use_tuple=False)
    control_params = get_control_parms(node, use_tuple=False)

    front_ratio, back_ratio = params.front_back_length_ratios
    angle = math.radians(control_params.posterior_outline_angle)
    width = control_params.half_width

    forward_height = width * front_ratio
    back_half = width * back_ratio
    back_length = math.sqrt(back_half * back_half + width * width) / (2.0 * math.sin(angle / 2.0))
    top_width = width * control_params.front_width_ratio

    p0 = hou.Vector3(0.0, 0.0, -forward_height)
    p1 = hou.Vector3(top_width, 0.0, -forward_height)
    p3 = hou.Vector3(width, 0.0, 0.0)
    p5 = hou.Vector3(0.0, 0.0, back_half)

    p3_p5_p4 = (math.pi - angle) / 2.0
    o_p3_p5 = math.atan2(back_half, width)
    o_p3_p4 = p3_p5_p4 + o_p3_p5
    p4 = p3 + back_length * hou.Vector3(-math.cos(o_p3_p4), 0.0, math.sin(o_p3_p4))

    p1_p3_x = p3[0] - p1[0]
    p1_p3_z = p3[2] - p1[2]
    p1_p3_length = math.sqrt(p1_p3_x * p1_p3_x + p1_p3_z * p1_p3_z)
    front_length = p1_p3_length / (2.0 * math.sin(angle / 2.0))

    midpoint_x = (p1[0] + p3[0]) / 2.0
    midpoint_z = (p1[2] + p3[2]) / 2.0
    midpoint_p2 = math.sqrt(front_length * front_length - p1_p3_length * p1_p3_length / 4.0)

    p2 = hou.Vector3(
        midpoint_x + p1_p3_z / p1_p3_length * midpoint_p2,
        0.0,
        midpoint_z - p1_p3_x / p1_p3_length * midpoint_p2,
    )

    replace_points(
        geo,
        [
            (sternumrim(index), position)
            for index, position in enumerate((p0, p1, p2, p3, p4, p5))
        ],
    )


def add_midpoints(node: hou.SopNode) -> None:
    geo = node.geometry()
    points = geo.points()
    assert len(points) >= 2

    for index in range(1, len(points) - 1):
        midpoint = (points[index].position() + points[index + 1].position()) / 2.0
        add_id_point(geo, midpoint, sternumrimmiddle(index))


def add_center_spine(node: hou.SopNode) -> None:
    geo = node.geometry()
    right_points = [point for point in geo.points() if point.position().x() > 0.0 + 1e-5]
    positions = [point.position() for point in right_points[1:]] # Exclude sternumrim1
    positions = sorted(positions, key=lambda p: p.z())

    for index, position in enumerate(positions, start=1):
        add_id_point(geo, hou.Vector3(0.0, 0.0, position[2]), sternumspine(index))


def descend_sternum_spine(node: hou.SopNode) -> None:
    geo = node.geometry()
    params = get_control_parms(node)

    ratio, power = params.spine_descent_spec
    depth = params.half_width * ratio

    points = points_by_id(geo)
    top, middle, bottom = positions_from_geo(
        geo,
        sternumrim(0),
        sternumrim(3),
        sternumrim(5),
    )

    upper_span = abs(middle[2] - top[2])
    lower_span = abs(bottom[2] - middle[2])
    assert upper_span != 0.0 and lower_span != 0.0
    for point_id, point in points.items():
        if not point_id.startswith(ID.STERNUMSPINE):
            continue
        position = point.position()
        rest_y = position[1]
        if position[2] <= middle[2]:
            y = _get_eased_depth(position[2], top[2], middle[2], rest_y, -depth, power)
        else:
            y = _get_eased_depth(position[2], bottom[2], middle[2], rest_y, -depth, power)
        point.setPosition((position[0], y, position[2]))


def _get_eased_depth(
    x: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    power: float,
) -> float:
    span = x1 - x0
    assert span != 0.0, "Expected non-zero span for easing interpolation"
    t = max(0.0, min(1.0, (x - x0) / span))
    return y0 + (y1 - y0) * (t ** power)
