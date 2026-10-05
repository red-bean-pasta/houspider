from hou import SopNode
from houkit.parameterizings.operator import add_float_parm


def add_parameters(base: SopNode) -> None:
    add_float_parm(
        base,
        "coxa_height_ratio",
        1,
        1.63,
        (0.0, None),
        label="Coxa Region Height",
        help="Coxa socket height relative to its width.",
    )


def add_controls(parent: SopNode) -> SopNode:
    control = parent.createNode("null", "CONTROLS")
    add_float_parm(
        control,
        "coxa_rise_angle",
        1,
        12,
        (0.0, 90.0),
        label="Coxa Region Rise",
        help="Raise coxa socket flaps. 0° to lie in the sternum plane; 90° to make it vertical.",
    )
    add_float_parm(
        control,
        "socket_membrane_ratio",
        3,
        (0.02, 0.1, 0.02),
        (0.0, None),
        label="Socket Membrane Width",
        help="X sets coxa socket side membrane width; Y sets upper; Z sets lower.",
    )
    add_float_parm(
        control,
        "dorsal_membrane_ratio",
        1,
        0.02,
        (0.0, None),
        label="Dorsal Membrane Width",
        help="Membrane width between dorsal and base, evaluated against coxa length.",
    )
    return control