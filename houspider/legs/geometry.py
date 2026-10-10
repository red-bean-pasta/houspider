import hou
from houkit.attributer import points_start_with
from houkit.noder import get_parent
from houkit.parameterizer import get_parms

from .attributes import Region
from ..bases import attributes as base_attributes
from ..helper import update_joint_limits


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
    update_joint_limits(
        node.geometry(),
        "leg_*",
        params.min_flex_angles,
        params.max_flex_angles,
        params.min_yaw_angles,
        params.max_yaw_angles,
        params.rest_flex_ratios,
    )



def cleanup(node: hou.SopNode) -> None:
    geo = node.geometry()
    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.LEGSEGMENT)
