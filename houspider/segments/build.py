from hou import Geometry, Point
from houkit.models import Moject

from . import membrane
from .attributing import attribute_segment_bases
from .models import LimbParam, LimbAttributes
from .segment import build_segment_tubes, inset_segment_thickness, add_segment_loop_cuts, close_tarsus
from .validation import validate_segment_loops


def build_segment_bases(
    geo: Geometry,
    param: LimbParam,
    attributes: LimbAttributes,
) -> Moject[tuple[list[Point], list[Point], list[Point]]]:
    """Build and attribute segment tubes, thickness loops, and membranes for a limb."""
    cube_pts, messages = build_segment_tubes(geo, param)
    thickness_pts = inset_segment_thickness(geo, cube_pts, param.support_loop_ratio)
    seg_pts = add_segment_loop_cuts(geo, cube_pts, param.support_loop_ratio)

    messages.extend(validate_segment_loops(seg_pts))

    mem_pts = membrane.fill_membranes(geo, thickness_pts)
    all_mem_pts = membrane.add_membrane_loop_cuts(
        geo,
        cube_pts,
        thickness_pts,
        mem_pts,
        param.support_loop_ratio,
    )
    close_tarsus(seg_pts, param.tarsus_wedge_angle)

    attribute_segment_bases(geo, attributes, seg_pts, thickness_pts, all_mem_pts)
    return Moject((seg_pts, thickness_pts, all_mem_pts), messages)
