import hou
from houkit.noder import (
    add_mirror,
    add_output,
    add_reloadable_subnet,
)

from houspider.helper import rename_left_ids_node, sopify_chain
from houspider.sternums.geos.face import build_sternum_faces, elevate_transition_loop, inset_transition_loop
from houspider.sternums.geos.frame import add_center_spine, add_midpoints, add_right_half, descend_sternum_spine
from houspider.sternums.geos.membrane import outset_sternum_loop
from houspider.sternums.parameters import add_controls, add_parameters


def build(prosoma: hou.SopNode) -> hou.SopNode:
    sternum = add_reloadable_subnet(prosoma, "sternum")
    add_parameters(sternum)
    add_controls(sternum)

    right_half = sopify_chain(
        sternum,
        None,
        (
            add_right_half,
            add_midpoints,
            add_center_spine,
            descend_sternum_spine,
        ),
    )
    mirror = add_mirror(sternum, "right_mirror", right_half, (1, 0, 0), True, False)
    buffered = sopify_chain(
        sternum,
        mirror,
        (
            rename_left_ids_node,
            build_sternum_faces,
            inset_transition_loop,
            elevate_transition_loop,
            outset_sternum_loop,
        ),
    )
    _ = add_output(sternum, "OUT_STERNUM", buffered)

    sternum.layoutChildren()
    return sternum
