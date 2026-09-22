import hou

from houkit.attributer import points_start_with

from ..bases import attributes as base_attributes
from ..segments.attributes import Region


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


def cleanup(node: hou.SopNode) -> None:
    geo = node.geometry()
    for prim in geo.prims():
        if not prim.stringAttribValue("region"):
            prim.setAttribValue("region", Region.LEGSEGMENT)
