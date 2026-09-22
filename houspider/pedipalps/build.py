import hou

from houkit.noder import add_fuse, add_mirror, add_output, add_reloadable_subnet, sopify
from houkit.parameterizer import add_float_parm, add_heading

from ..helper import rename_left_ids_node, sopify_chain
from . import topology


def build(
    parent: hou.SopNode,
    base: hou.SopNode,
    legs: hou.SopNode,
) -> hou.SopNode:
    pedipalp = add_reloadable_subnet(parent, "pedipalps")
    pedipalp.setInput(0, base)
    pedipalp.setInput(1, legs)
    add_parameters(pedipalp)
    _add_controls(pedipalp)

    cleaned_up = sopify_chain(
        pedipalp,
        pedipalp.indirectInputs()[0],
        (
            topology.remove_noise_points,
            topology.build_basic,
            topology.trim_bottom_side_length,
            topology.position_basic,
            topology.delete_start_coxa_supports,
            topology.prepare_coxa_base_trapezoid,
            topology.fill_bottom_right_face,
            topology.fill_back_face,
            topology.fill_top_face,
            topology.add_front_upper_face,
            topology.add_front_loop_faces,
            topology.add_maxilla_quads,
            topology.fill_maxilla_faces,
            topology.cleanup,
        ),
    )
    fused = add_fuse(pedipalp, "fuse_sockets", cleaned_up)
    mirrored = add_mirror(pedipalp, "mirror_left_pedipalps", fused, (1, 0, 0), True, False)
    renamed = sopify(pedipalp, mirrored, rename_left_ids_node)
    add_output(pedipalp, "OUT_PEDIPALPS", renamed)
    pedipalp.layoutChildren()
    return pedipalp


def add_parameters(subnet: hou.OpNode) -> None:
    add_heading(
        subnet,
        "Pedipalp",
    )
    add_float_parm(
        subnet,
        "pedipalp_coxa_length",
        default=0.8,
        min_max=(0.0, None),
        label="Coxa Length",
        help="Coxa length evaluated against front leg coxa length.",
    )
    add_float_parm(
        subnet,
        "pedipalp_segment_length_ratios",
        5,
        (0.17, 0.8, 0.4, 0.45, 0.4),
        (0.0, None),
        hou.parmNamingScheme.Base1,
        label="Other Segment Lengths",
        help="One length ratio per post-coxa pedipalps segment, measured against pedipalps coxa length.",
    )
    add_float_parm(
        subnet,
        "endite_length_ratio",
        default=0.95,
        min_max=(0.0, None),
        label="Endite Length",
        help="Extension from the endite membrane attachment toward the coxa.",
    )


def _add_controls(parent: hou.SopNode) -> hou.SopNode:
    control = parent.createNode("null", "CONTROL")
    add_float_parm(
        control,
        "endite_buffer_ratios",
        size=2,
        default=(0.4, 0.1),
        min_max=(0.0, 1.0),
        label="Endite Buffer",
        help="X positions the buffer across the coxa end; Y sets its lengthwise reach.",
    )
    add_float_parm(
        control,
        "endite_surface_size_ratio",
        default=0.06,
        min_max=(0.0, 1.0),
        label="Endite Surface Size",
        help="Size of the added endite surface faces.",
    )
    return control
