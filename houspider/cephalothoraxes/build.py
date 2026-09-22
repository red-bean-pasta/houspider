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
from ..heads.build import build as build_head
from ..mouths.build import build as build_mouth
from ..spiders import topology


def build(spider: hou.OpNode) -> hou.SopNode:
    cephalothorax = add_reloadable_subnet(spider, "cephalothorax")
    _add_parameters(cephalothorax)

    base = build_base(cephalothorax)

    head = build_head(cephalothorax, base)

    b_h_merge = add_merge(cephalothorax, "merge_base_and_head", base, head)
    b_h_fuse = add_fuse(cephalothorax, "fuse_base_and_head", b_h_merge)

    mouth = build_mouth(cephalothorax, b_h_fuse)
    chelicerae = build_chelicerae(cephalothorax, mouth)

    recalculate = add_recalculate_normal(cephalothorax, "recalculate_normals", chelicerae)
    positioned = _position_cephalothorax(cephalothorax, recalculate)
    opened = sopify(cephalothorax, positioned, topology.open_cepha_pedicel)

    _ = add_output(cephalothorax, "OUT_CEPHALOTHORAX", opened)

    cephalothorax.layoutChildren()
    return cephalothorax


def _add_parameters(cephalothorax: hou.SopNode) -> None:
    add_float_parm(
        cephalothorax,
        "pedicel_opening_ratios",
        2,
        (0.5, 0.5),
        (0.0, 1.0),
        label="Pedicel Opening",
        help="X sets the side and upper opening proportion. Y places the lower opening between the base end and sternum rim.",
    )


def _position_cephalothorax(parent: hou.SopNode, source: hou.SopNode) -> hou.SopNode:
    position = parent.createNode("xform", "position_cephalothorax")
    position.setInput(0, source)
    pattern = f'pointpattern(0, "@id={base_attributes.baseend(0)}")'
    for axis_index, axis_name in enumerate(("tx", "ty", "tz")):
        position.parm(axis_name).setExpression(f'0 - point(0, {pattern}, "P", {axis_index})')
    return position
