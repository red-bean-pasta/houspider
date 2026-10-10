import hou
from houkit.attributer import points_start_with
from houkit.noder import get_parent
from houkit.parameterizer import get_parms
from houkit.topologies.basic import remove_unused_points

from .attributes import Region
from ..attributes import GlobalAttrib
from ..bases.attributes import basemaxillamembrane
from ..models import JointLimits


def remove_noise_points(
    node: hou.SopNode,
) -> None:
    geo = node.geometry()

    pts = points_start_with(geo, "id", basemaxillamembrane())
    geo.deletePoints(list(p for p in geo.points() if p not in pts))


def cleanup(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()

    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.PEDIPALPSEGMENT)

    remove_unused_points(geo)


def record_global_info(
    node: hou.SopNode,
) -> None:
    parent = get_parent(node)
    params = get_parms(parent)

    legs_geo = node.inputGeometry(1)
    assert legs_geo and legs_geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS), (
        "Expected legs geometry with joint_limits at input 1"
    )
    leg_limits = JointLimits.from_geometry(legs_geo, "leg_*")

    # Pedipalps lack a metatarsus: map joints (coxa, trochanter, femur, patella, tibia, tarsus)
    pedipalp_indices = (0, 1, 2, 3, 4, 6)
    pedipalp_limits = leg_limits.select(pedipalp_indices, params.rest_flex_ratios)
    pedipalp_limits.write_to_geometry(node.geometry(), "pedipalp_*")


