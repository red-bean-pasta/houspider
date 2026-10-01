import hou
from houkit.attributer import points_start_with
from houkit.topologies.basic import remove_unused_points

from .attributes import Region
from ..bases.attributes import basemaxillamembrane


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
