import hou
from houkit.parameterizings.operator import add_folder

from houkit.noder import (
    add_merge_fuse,
    add_output,
    add_reloadable_subnet,
    sopify,
)
from houkit.parameterizer import add_float_parm

from . import pedicel
from ..bases import attributes as base_attributes
from ..bases.build import build as build_base
from ..cheliceraes.build import build as build_chelicerae
from ..dorsals.build import build as build_dorsal
from ..mouths.build import build as build_mouth
from ..sternums.build import build as build_sternum


def build(spider: hou.OpNode) -> hou.SopNode:
    prosoma = add_reloadable_subnet(spider, "prosoma")
    _add_parameters(prosoma)

    sternum = build_sternum(prosoma)
    base = build_base(prosoma, sternum)

    s_c_fuse = add_merge_fuse(prosoma, "merge_fuse_sternum_and_coxa", base, sternum)

    dorsal = build_dorsal(prosoma, s_c_fuse)

    b_d_fuse = add_merge_fuse(prosoma, "merge_fuse_base_and_dorsal", s_c_fuse, dorsal)

    mouth = build_mouth(prosoma, b_d_fuse)
    chelicerae = build_chelicerae(prosoma, mouth)

    positioned = _position_prosoma(prosoma, chelicerae)
    opened = sopify(prosoma, positioned, pedicel.open_prosoma_pedicel)

    _ = add_output(prosoma, "OUT_PROSOMA", opened)

    prosoma.layoutChildren()
    return prosoma


def _add_parameters(prosoma: hou.SopNode) -> None:
    add_folder(
        prosoma,
        "pedicel",
        folder_type=hou.folderType.Collapsible,
    )
    add_float_parm(
        prosoma,
        "pedicel_opening_ratios",
        2,
        (0.5, 0.5),
        (0.0, 1.0),
        label="Pedicel Opening",
        folder_label="Pedicel",
        help="X sets the side and upper opening proportion. Y places the lower opening between the base end and sternum rim.",
    )


def _position_prosoma(parent: hou.SopNode, source: hou.SopNode) -> hou.SopNode:
    position = parent.createNode("xform", "position_prosoma")
    position.setInput(0, source)
    pattern = f'pointpattern(0, "@id={base_attributes.baseend(0)}")'
    for axis_index, axis_name in enumerate(("tx", "ty", "tz")):
        position.parm(axis_name).setExpression(f'0 - point(0, {pattern}, "P", {axis_index})')
    return position
