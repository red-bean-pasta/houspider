from hou import SopNode
from houkit.parameterizings.operator import add_float_parm


def add_parameters(sternum: SopNode) -> None:
    add_float_parm(
        sternum,
        "front_back_length_ratios",
        2,
        (1.85, 1.6),
        (0.0, None),
        label="Front / Back Length",
        help="X for anterior length; Y for posterior length; Both relative to sternum half-width.",
    )


def add_controls(parent: SopNode) -> SopNode:
    control = parent.createNode("null", "CONTROLS")
    add_float_parm(
        control,
        "half_width",
        1,
        100.0,
        label="Half Width",
        help="Half width of sternum widest span",
    )
    add_float_parm(
        control,
        "front_width_ratio",
        1,
        0.455,
        (0.0, 1.0),
        label="Front Width",
        help="Anterior width relative to the widest span.",
    )
    add_float_parm(
        control,
        "posterior_outline_angle",
        1,
        150.0,
        (0.0, 180.0),
        label="Posterior Outline Angle",
        help="Interior angle that shapes the rear sternum outline.",
    )
    add_float_parm(
        control,
        "spine_descent_spec",
        2,
        (0.25, 0.75),
        (0.0, None),
        label="Spine Depth",
        help="X for spine lowest point depth evaluated against sternum half-width; Y for spine descent power.",
    )
    add_float_parm(
        control,
        "transition_loop_position",
        2,
        (0.8, 0.35),
        (0.0, 1.0),
        label="Transition Loop Position",
        help="X for positional ratio from center spine towards rim. Y for elevation ratio relative to spine depth. If X is 1, the loop is omitted."
    )
    add_float_parm(
        control,
        "membrane_ratio",
        1,
        0.02,
        (0.0, None),
        label="Membrane Width",
        help="Width relative to sternum half-width for the outest membrane connected to dorsal.",
    )
    return control