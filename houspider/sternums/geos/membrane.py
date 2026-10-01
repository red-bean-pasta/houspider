import hou
from houkit.attributer import deduplicate_point_attribs
from houkit.topology import outset

from houspider.helper import get_control_parms, points_by_id
from houspider.sternums.attributes import outer_rim_ids, sternumrimmiddle, sternumrim


def outset_sternum_loop(node: hou.SopNode) -> None:
    geo = node.geometry()
    params = get_control_parms(node)
    dist = params.membrane_ratio * params.half_width

    _add_sternum_loop(geo, dist)
    _add_sternum_loop(geo, dist)
    _adjust_midpoints_after_outset(geo)


def _add_sternum_loop(geo: hou.Geometry, dist: float) -> None:
    outset(list(geo.prims()), dist, use_ratio=False)
    deduplicate_point_attribs(geo, "id", outer_rim_ids(), keep_first=False)


def _adjust_midpoints_after_outset(geo: hou.Geometry) -> None:
    points = points_by_id(geo)

    def position(point_id: str) -> hou.Vector3:
        return points[point_id].position()

    for side in (1, -1):
        for i in range(1, 5):
            start_id = sternumrim(side * i)
            end_id = sternumrim(5 if i == 4 else side * (i + 1))

            midpoint = (position(start_id) + position(end_id)) / 2.0
            points[sternumrimmiddle(side * i)].setPosition(midpoint)
