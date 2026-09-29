import hou

from houkit.noder import (
    add_fuse,
    add_output,
    add_reloadable_subnet,
)
from houkit.parameterizer import add_float_parm
from . import topology
from ..helper import sopify_chain


def build(prosoma: hou.SopNode, sternum: hou.SopNode) -> hou.SopNode:
    base = add_reloadable_subnet(prosoma, "base")
    base.setInput(0, sternum)
    _add_parameters(base)

    sternum_source = base.indirectInputs()[0]

    flap_regions = sopify_chain(
        base,
        sternum_source,
        (topology.extract_sternum_rim, topology.build_coxa_flaps, topology.add_flap_regions),
    )
    fuse_flaps = add_fuse(base, "fuse_coxa_flaps", flap_regions)
    connected = sopify_chain(
        base,
        fuse_flaps,
        (topology.connect_side_flaps, topology.adjust_front_and_end_flaps),
    )
    fuse_connected = add_fuse(base, "fuse_connected_side_flaps", connected)
    pedicel = sopify_chain(
        base,
        fuse_connected,
        (
            topology.cleanup_connected_side_flap_ids,
            topology.rotate_coxa_flaps,
            topology.adjust_frontest_line,
            topology.fill_maxilla,
            topology.fill_pedicel_membrane,
        ),
    )

    fused_pedicel = add_fuse(base, "fuse_pedicel_membrane", pedicel)
    membrane = sopify_chain(
        base,
        fused_pedicel,
        (topology.adjust_mouth, topology.inset_membrane),
    )

    buffered = sopify_chain(
        base,
        membrane,
        (topology.extrude_base_buffer, topology.remove_coxa_sockets),
    )
    add_output(base, "OUT_BASE", buffered)

    base.layoutChildren()
    return base


def _add_parameters(base: hou.SopNode) -> None:
    add_float_parm(
        base,
        "coxa_flap_extension_ratio",
        1,
        1.63,
        (0.0, None),
        label="Coxa Flap Extension",
        help="Outward reach from the sternum rim, relative to rim-edge length.",
    )
    add_float_parm(
        base,
        "coxa_flap_rise_angle",
        1,
        12,
        (0.0, 90.0),
        label="Coxa Flap Rise",
        help="0° lies in the sternum plane; 90° raises the flap edge vertically.",
    )
    add_float_parm(
        base,
        "membrane_ratio",
        3,
        (0.02, 0.1, 0.02),
        (0.0, None),
        label="Membrane Width",
        help="X (1st) sets side membrane width. Y (2nd) sets upper membrane width. Z (3rd) sets lower membrane width.",
    )
