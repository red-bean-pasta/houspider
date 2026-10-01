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
) -> Moject[tuple[list[list[Point]], list[Point], list[Point]]]:
    """Build and attribute segment tubes, thickness loops, and membranes for a limb."""
    segment_tubes, messages = build_segment_tubes(geo, param)
    thickness_pts = inset_segment_thickness(geo, segment_tubes, param.support_loop_ratio)
    seg_tubes = add_segment_loop_cuts(geo, segment_tubes, param.support_loop_ratio)

    messages.extend(validate_segment_loops(seg_tubes))

    mem_pts = membrane.fill_membranes(geo, thickness_pts)
    all_mem_pts = membrane.add_membrane_loop_cuts(
        geo,
        segment_tubes,
        thickness_pts,
        mem_pts,
        param.support_loop_ratio,
    )
    close_tarsus(seg_tubes[-1], param.tarsus_wedge_angle)

    attribute_segment_bases(geo, attributes, seg_tubes, thickness_pts, all_mem_pts)
    return Moject((seg_tubes, thickness_pts, all_mem_pts), messages)
