import hou
from houkit.noder import (
    add_output,
    add_reloadable_subnet,
)

from houspider.bases.geos.membrane import inset_coxa, adjust_coxa_membrane_points, inset_labium, inset_maxilla, adjust_maxilla_upper_membrane, extrude_base_buffer, remove_coxa_sockets
from houspider.bases.parameters import add_parameters, add_controls
from houspider.bases.geos.coxa import (
    extrude_sternum_rim,
    rotate_middle_edges,
    rotate_coxa_flaps,
    correct_rim_edges,
    correct_coxa_shape,
)
from houspider.bases.geos.front import align_labium, adjust_labium_position, fill_maxilla, fill_pedicel_membrane
from houspider.helper import sopify_chain


def build(prosoma: hou.SopNode, sternum: hou.SopNode) -> hou.SopNode:
    base = add_reloadable_subnet(prosoma, "base")
    base.setInput(0, sternum)

    add_parameters(base)
    add_controls(base)

    built = sopify_chain(
        base,
        base.indirectInputs()[0],
        (
            extrude_sternum_rim,
            rotate_middle_edges,
            rotate_coxa_flaps,
            correct_rim_edges,
            correct_coxa_shape,
            align_labium,
            adjust_labium_position,
            fill_maxilla,
            fill_pedicel_membrane,
            inset_coxa,
            adjust_coxa_membrane_points,
            inset_labium,
            inset_maxilla,
            adjust_maxilla_upper_membrane,
            extrude_base_buffer,
            remove_coxa_sockets,
        ),
    )
    add_output(base, "OUT_BASE", built)

    base.layoutChildren()
    return base

