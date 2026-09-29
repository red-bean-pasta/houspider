import hou

from ..bases import attributes as base_attributes
from houkit.noder import (
    add_fuse,
    add_merge,
    add_output,
    add_recalculate_normal,
    add_reloadable_subnet,
    sopify,
)
from houkit.parameterizer import add_float_parm

from ..bases.build import build as build_base
from ..cheliceraes.build import build as build_chelicerae
from ..dorsals.build import build as build_dorsal
from ..mouths.build import build as build_mouth
from ..spiders import topology


def build(spider: hou.OpNode) -> hou.SopNode:
    prosoma = add_reloadable_subnet(spider, "prosoma")
    _add_parameters(prosoma)

    base = build_base(prosoma)

    dorsal = build_dorsal(prosoma, base)

    b_d_merge = add_merge(prosoma, "merge_base_and_dorsal", base, dorsal)
    b_d_fuse = add_fuse(prosoma, "fuse_base_and_dorsal", b_d_merge)

    mouth = build_mouth(prosoma, b_d_fuse)
    chelicerae = build_chelicerae(prosoma, mouth)

    recalculate = add_recalculate_normal(prosoma, "recalculate_normals", chelicerae)
    positioned = _position_prosoma(prosoma, recalculate)
    opened = sopify(prosoma, positioned, topology.open_prosoma_pedicel)

    _ = add_output(prosoma, "OUT_PROSOMA", opened)

    prosoma.layoutChildren()
    return prosoma


def _add_parameters(prosoma: hou.SopNode) -> None:
    add_float_parm(
        prosoma,
        "pedicel_opening_ratios",
        2,
        (0.5, 0.5),
        (0.0, 1.0),
        label="Pedicel Opening",
        help="X sets the side and upper opening proportion. Y places the lower opening between the base end and sternum rim.",
    )


def _position_prosoma(parent: hou.SopNode, source: hou.SopNode) -> hou.SopNode:
    position = parent.createNode("xform", "position_prosoma")
    position.setInput(0, source)
    pattern = f'pointpattern(0, "@id={base_attributes.baseend(0)}")'
    for axis_index, axis_name in enumerate(("tx", "ty", "tz")):
        position.parm(axis_name).setExpression(f'0 - point(0, {pattern}, "P", {axis_index})')
    return position
