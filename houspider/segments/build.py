import hou
from houkit.attributer import add_prim_attrib
from houkit.models import Moject

from . import membrane, segment
from .attributes import LegParam


def build_leg(
    geo: hou.Geometry,
    param: LegParam,
) -> Moject[tuple[list[hou.Point], list[hou.Point], list[hou.Point]]]:
    add_prim_attrib(geo, "region", "")

    cube_pts, warnings = segment.build_segment_bases(geo, param)
    thickness_pts = segment.inset_segment_thickness(geo, cube_pts, param.support_loop_ratio)
    seg_pts = segment.add_segment_loop_cuts(geo, cube_pts, param.support_loop_ratio)
    mem_pts = membrane.fill_membranes(geo, thickness_pts)
    all_mem_pts = membrane.add_membrane_loop_cuts(
        geo,
        cube_pts,
        thickness_pts,
        mem_pts,
        param.support_loop_ratio,
    )
    membrane.close_tarsus(geo, seg_pts, param.tarsus_wedge_angle)
    return Moject((seg_pts, thickness_pts, all_mem_pts), warnings)
