import hou
from houkit.attributer import points_start_with
from houkit.noder import get_parent
from houkit.parameterizer import get_parms

from .attributes import Region
from ..bases import attributes as base_attributes
from ..models import JointLimits


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
    params = get_parms(parent)
    limits = JointLimits(
        min_flex=tuple(params.min_flex_angles),
        max_flex=tuple(params.max_flex_angles),
        min_yaw=tuple(params.min_yaw_angles),
        max_yaw=tuple(params.max_yaw_angles),
        rest_ratios=tuple(params.rest_flex_ratios),
    )
    limits.write_to_geometry(node.geometry(), "leg_*")



def cleanup(node: hou.SopNode) -> None:
    geo = node.geometry()
    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.LEGSEGMENT)
