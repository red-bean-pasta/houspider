import hou
from houkit.formatter import title_case

from houkit.noder import (
    add_fuse,
    add_mirror,
    add_output,
    add_reloadable_subnet,
    sopify,
)
from houkit.parameterizer import add_float_parm

from ..attributes import LegSegment
from houspider.helper import rename_left_ids_node, sopify_chain
from . import topology


def build(
    spider: hou.SopNode,
    base: hou.SopNode,
) -> hou.SopNode:
    legs = add_reloadable_subnet(spider, "legs")
    legs.setInput(0, base)
    _add_parameters(legs)
    _add_controls(legs)

    cleaned_up = sopify_chain(
        legs,
        legs.indirectInputs()[0],
        (
            topology.record_global_info,
            topology.extract_right_leg_points,
            topology.build_basic,
            topology.position_basic,
            topology.adjust_coxa_start,
            topology.fill_coxa_upper_pentagon,
            topology.fill_coxa_bottom_pentagon,
            topology.fill_coxa_back_faces,
            topology.fill_coxa_front_faces,
            topology.cleanup,
        ),
    )
    fused = add_fuse(legs, "fuse_sockets", cleaned_up)
    mirrored = add_mirror(legs, "mirror_left_legs", fused, (1, 0, 0), True, False)
    renamed = sopify(legs, mirrored, rename_left_ids_node)
    add_output(legs, "OUT_LEGS", renamed)

    legs.layoutChildren()
    return legs


def _add_parameters(legs: hou.OpNode) -> None:
    add_float_parm(
        legs,
        "coxa_length_ratio",
        1,
        1.2,
        (0.0, None),
        label="Coxa Length",
        help="Front coxa length evaluated against front socket width.",
    )
    add_float_parm(
        legs,
        "segment_length_ratios",
        6,
        (0.33, 1.5, 0.9, 1.2, 1, 0.7),
        (0.0, None),
        hou.parmNamingScheme.Base1,
        label="Segment Lengths",
        help="One length ratio per post-coxa segment, measured against front coxa length.",
    )
    _add_segment_parameters(legs)
    add_float_parm(
        legs,
        "tarsus_wedge_angle",
        1,
        45.0,
        (-60.0, 60.0),
        label="Tarsus Wedge",
        help="Terminal tarsus wedge angle.",
    )
    add_float_parm(
        legs,
        "min_flex_angles",
        7,
        (140, 180, 200, 30, 150, 95, 170),
        (0.0, None),
        hou.parmNamingScheme.Base1,
        label="Minimum Flex Angles",
        help="One minimum flex angle per segment joint.",
    )
    add_float_parm(
        legs,
        "max_flex_angles",
        7,
        (220, 180, 270, 160, 190, 178, 190),
        (0.0, None),
        hou.parmNamingScheme.Base1,
        label="Maximum Flex Angles",
        help="One maximum flex angle per segment joint.",
    )
    add_float_parm(
        legs,
        "min_yaw_angles",
        7,
        (-15, -25, 0, 0, 0, 0, -20),
        (None, None),
        hou.parmNamingScheme.Base1,
        label="Minimum Yaw Angles",
        help="One minimum yaw angle per segment joint.",
    )
    add_float_parm(
        legs,
        "max_yaw_angles",
        7,
        (15, 25, 0, 0, 0, 0, 20),
        (0.0, None),
        hou.parmNamingScheme.Base1,
        label="Maximum Yaw Angles",
        help="One maximum yaw angle per segment joint.",
    )
    add_float_parm(
        legs,
        "leg_width_ratios",
        3,
        (0.8, 0.7, 0.8),
        (0.0, None),
        label="Other Leg Widths",
        help="Width scales relative to the front leg for the 2nd-4th legs.",
    )
    add_float_parm(
        legs,
        "leg_length_ratios",
        3,
        (0.88, 0.9, 1.1),
        (0.0, None),
        label="Other Leg Lengths",
        help="Length scales relative to the front leg for the 2nd-4th legs.",
    )


def _add_segment_parameters(legs: hou.OpNode) -> None:
    ptg = legs.parmTemplateGroup()
    folder = hou.FolderParmTemplate(
        "segments",
        "Segments",
        folder_type=hou.folderType.Collapsible,
    )
    segment_specs = (
        (LegSegment.COXA, ((0.0, 0.9, 0.75), (1.0, 0.85, 0.7))),
        (LegSegment.TROCHANTER, ((0.0, 0.9, 0.9), (1.0, 0.95, 1.1))),
        (LegSegment.FEMUR, ((0.0, 0.95, 0.95), (1.0, 1.0, 1.0))),
        (LegSegment.PATELLA, ((0.0, 1.0, 1.0), (1.0, 1.0, 1.0))),
        (LegSegment.TIBIA, ((0.0, 1.0, 1.0), (1.0, 1.0, 1.0))),
        (LegSegment.METATARSUS, ((0.0, 1.0, 1.0), (1.0, 1.0, 1.0))),
        (LegSegment.TARSUS, ((0.0, 1.0, 1.0), (1.0, 1.0, 1.0))),
    )
    for name, _ in segment_specs:
        label = title_case(name)
        mp = hou.FolderParmTemplate(
            f"{name}_sections",
            label,
            folder_type=hou.folderType.MultiparmBlock,
        )
        mp.setDefaultValue(2)
        vec_template = hou.FloatParmTemplate(
            f"{name}_section#",
            "Section #",
            3,
            default_value=(0.0, 1.0, 1.0),
            help=(
                "(position, width, height)\n"
                "- position: Length ratio along segment from 0.0 (start) to 1.0 (end).\n"
                "- width: Width multiplier against preceding segment's end section (or socket).\n"
                "- height: Height multiplier against preceding segment's end section (or socket)."
            ),
        )
        mp.setParmTemplates([vec_template])
        folder.addParmTemplate(mp)

    ptg.append(folder)
    legs.setParmTemplateGroup(ptg)

    for name, defaults in segment_specs:
        for idx, val in enumerate(defaults):
            legs.parmTuple(f"{name}_section{idx + 1}").set(val)


def _add_controls(parent: hou.SopNode) -> hou.SopNode:
    control = parent.createNode("null", "CONTROL")
    add_float_parm(
        control,
        "coxa_start_wedge_angle",
        1,
        45.0,
        (0.0, 90.0),
        label="Coxa Start Wedge",
        help="Wedge angle used to place the coxa socket's lower support.",
    )
    add_float_parm(
        control,
        "segment_spine_ratio",
        1,
        0.4,
        (0.0, None),
        label="Segment Spine Ratio",
        help="Moves the segment’s fullest area between its upper and lower sides.",
    )
    add_float_parm(
        control,
        "joint_clearance_limits",
        3,
        (1.0, 5.0, 45.0),
        (0.0, 90.0),
        hou.parmNamingScheme.Base1,
        label="Joint Clearance Limits",
        help="1: Minimum membrane separation. 2: Minimum wedge angle. 3: Maximum wedge angle.",
    )
    add_float_parm(
        control,
        "joint_support_loop_ratio",
        1,
        0.015,
        (0.0, 1.0),
        label="Joint Support Loop",
        help="Inset width at coxa sockets and segment joints, relative to coxa width.",
    )
    return control
