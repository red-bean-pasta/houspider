import hou

from houkit.noder import (
    add_merge_fuse,
    add_mirror,
    add_output,
    add_reloadable_subnet,
    sopify,
)
from houkit.parameterizer import add_float_parm
from ..helper import rename_left_ids_node, sopify_chain
from . import topology


def build(prosoma: hou.SopNode, base: hou.SopNode) -> hou.SopNode:
    dorsal = add_reloadable_subnet(prosoma, "dorsal")
    dorsal.setInput(0, base)
    _add_parameters(dorsal)
    _add_controls(dorsal)

    source = dorsal.indirectInputs()[0]
    base_rim = sopify(dorsal, source, topology.extract_base_rim)
    base_points = sopify(dorsal, source, topology.extract_work_base)
    regions = sopify_chain(
        dorsal,
        base_points,
        (
            topology.add_corners_half,
            topology.add_dorsal_dent,
            topology.curve_lip,
            topology.fill_back_loop_faces,
            topology.fill_support_loop_faces,
            topology.fill_side_faces,
            topology.add_side_regions,
        ),
    )
    mirrored = add_mirror(dorsal, "left_mirror", regions, (1, 0, 0), True, False)
    faces = sopify(dorsal, mirrored, rename_left_ids_node)

    fused = add_merge_fuse(dorsal, "merge_fuse_base_rim", base_rim, faces)
    cleaned = sopify_chain(
        dorsal,
        fused,
        (topology.inset_base_support_loop, topology.extrude_lip, topology.cleanup),
    )
    add_output(dorsal, "OUT_DORSAL", cleaned)
    dorsal.layoutChildren()
    return dorsal


def _add_parameters(dorsal: hou.SopNode) -> None:
    add_float_parm(
        dorsal,
        "height_ratio",
        1,
        0.375,
        (0.0, None),
        label="Top Height",
        help="Top-face height relative to the base-to-chelicerae reference span.",
    )
    add_float_parm(
        dorsal,
        "top_width_length_ratios",
        2,
        (1.0, 0.4),
        (0.0, None),
        naming_scheme=hou.parmNamingScheme.XYZW,
        label="Top Width / Length",
        help="X sets top width. Y sets the top face’s front-to-back length and flatness.",
    )
    add_float_parm(
        dorsal,
        "top_face_offset_ratio",
        1,
        0.0,
        label="Top Face Offset",
        help="Lengthwise skew of the top face relative to base length.",
    )
    add_float_parm(
        dorsal,
        "top_support_loop_ratios",
        2,
        (0.2, 0.5),
        naming_scheme=hou.parmNamingScheme.Base1,
        label="Top Support Loop",
        help="X adjusts the forward portion; Y adjusts the rear portion between the top face and base-side loop.",
    )
    add_float_parm(
        dorsal,
        "chelicerae_height_ratio",
        1,
        0.35,
        (0.0, None),
        label="Chelicerae Height",
        help="Vertical placement of the upper chelicerae line relative to the base.",
    )
    add_float_parm(
        dorsal,
        "lip_extrusion_ratio",
        2,
        (5.0, 1.0),
        (-10.0, 10.0),
        naming_scheme=hou.parmNamingScheme.XYZW,
        label="Lip Extrusion",
        help="X is lengthwise extrusion; Y is vertical extrusion.",
    )


def _add_controls(parent: hou.SopNode) -> hou.SopNode:
    control = parent.createNode("null", "CONTROL")
    add_float_parm(
        control,
        "membrane_ratio",
        1,
        0.035,
        (0.0, None),
        label="Membrane Width",
        help="Shared prosoma setting. Each region applies it against its own local membrane scale.",
    )
    return control
