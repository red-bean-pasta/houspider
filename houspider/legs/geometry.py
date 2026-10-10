import hou
from houkit.attributer import add_global_attrib, points_start_with
from houkit.noder import get_parent
from houkit.parameterizer import get_parms

from .attributes import Region
from ..attributes import GlobalAttrib
from ..bases import attributes as base_attributes


def extract_right_leg_points(node: hou.SopNode) -> None:
    geo = node.geometry()
    points = points_start_with(
        geo,
        "id",
        (
            base_attributes.basecoxamemebrane(),
            base_attributes.basecoxamembranemiddle(),
        ),
    )
    used = [point for point in points if point.position().x() > 0]
    geo.deletePoints([point for point in geo.points() if point not in used])
    geo.deletePrims(geo.prims(), keep_points=True)


def record_global_info(
    node: hou.SopNode,
) -> None:
    parent = get_parent(node)
    geo = node.geometry()

    params = get_parms(parent)
    min_flex = tuple(params.min_flex_angles)
    max_flex = tuple(params.max_flex_angles)
    min_yaw = tuple(params.min_yaw_angles)
    max_yaw = tuple(params.max_yaw_angles)
    rest_ratios = tuple(params.rest_flex_ratios)
    rest_flex = tuple(
        lo + r * (hi - lo)
        for lo, hi, r in zip(min_flex, max_flex, rest_ratios)
    )

    joint_limits = {
        "leg_*": {
            "min_flex_angles": min_flex,
            "max_flex_angles": max_flex,
            "min_yaw_angles": min_yaw,
            "max_yaw_angles": max_yaw,
            "rest_flex_ratios": rest_ratios,
            "rest_flex_angles": rest_flex,
        }
    }
    limits_attrib = add_global_attrib(
        geo,
        GlobalAttrib.JOINT_LIMITS,
        joint_limits,
    )
    geo.setGlobalAttribValue(limits_attrib, joint_limits)


def cleanup(node: hou.SopNode) -> None:
    geo = node.geometry()
    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.LEGSEGMENT)
