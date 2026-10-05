import hou

from houkit.noder import (
    add_merge,
    add_merge_fuse,
    add_mirror,
    add_output,
    add_reloadable_subnet,
    sopify,
)
from houkit.parameterizer import add_float_parm
from ..helper import rename_left_ids_node, sopify_chain
from . import topology


def build(spider_node: hou.OpNode, prosoma: hou.SopNode) -> hou.SopNode:
    abdomen = add_reloadable_subnet(spider_node, "abdomen")
    abdomen.setInput(0, prosoma)
    _add_parameters(abdomen)
    _add_controls(abdomen)

    source = abdomen.indirectInputs()[0]
    prosoma_info = sopify(abdomen, source, topology.prepare_prosoma_info)
    width_frame = sopify(abdomen, prosoma_info, topology.add_width_frame)
    height_frame = sopify(abdomen, prosoma_info, topology.add_height_frame)

    fused = add_merge_fuse(abdomen, "merge_fuse_frames", width_frame, height_frame)
    lower_middle_frame = sopify_chain(abdomen, fused, (topology.add_upper_middle_frame, topology.add_lower_middle_frame))
    right_side_faces = sopify(abdomen, lower_middle_frame, topology.fill_right_side_faces)

    # Kept for in-editor debug and visualize purpose
    connected = sopify(abdomen, lower_middle_frame, topology.connect_frames_tmp)
    _ = add_merge(abdomen, "debug_merge_frames_and_points", lower_middle_frame, connected)

    mirrored = add_mirror(abdomen, "mirror_left_faces", right_side_faces, (1, 0, 0), True, False)
    renamed = sopify(abdomen, mirrored, rename_left_ids_node)
    cleaned = sopify_chain(abdomen, renamed, (topology.add_regions, topology.cleanup_temp_attributes))

    opened = sopify(abdomen, cleaned, topology.open_abdomen_pedicel)
    add_output(abdomen, "OUT_ABDOMEN", opened)
    abdomen.layoutChildren()
    return abdomen


def _add_parameters(abdomen: hou.SopNode) -> None:
    add_float_parm(
        abdomen,
        "size_ratios",
        3,
        (1.2, 1.0, 1.2),
        (0.0, None),
        label="Width / Height / Length",
        help="Abdomen width, height, and length against the prosoma.",
    )
    add_float_parm(
        abdomen,
        "width_hold_ratios",
        2,
        (0.1, 0.6),
        (0.0, None),
        label="Constant Width Range",
        help="X and Y mark where the constant-width region starts and ends along abdomen length.",
    )


def _add_controls(parent: hou.SopNode) -> hou.SopNode:
    control = parent.createNode("null", "CONTROL")
    add_float_parm(
        control,
        "end_size_ratio",
        1,
        0.2,
        (0.0, None),
        label="End Size",
        help="Terminal width and height relative to the abdomen’s maximum size.",
    )
    return control
