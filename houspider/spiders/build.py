import hou
from typing import Any

from houkit.noder import (
    add_merge,
    add_merge_fuse,
    add_recalculate_normal,
    add_reloadable_subnet,
    sopify,
)
from houkit.nodes.sops import add_output
from ..attributes import GlobalAttrib
from ..abdomens.build import build as build_abdomen
from ..legs.build import build as build_legs
from ..pedicels.build import build as build_pedicel
from ..pedipalps.build import build as build_pedipalps
from ..prosomas.build import build as build_prosoma


def build(parent: hou.OpNode, name: str = "spider") -> hou.SopNode:
    spider = _add_spider(parent, name)

    prosoma = build_prosoma(spider)

    abdomen_node = build_abdomen(spider, prosoma)
    merged_p_a = add_merge(spider, "merge_prosoma_and_abdomen", prosoma, abdomen_node)
    pedicel = build_pedicel(spider, merged_p_a)
    fused_pa_p = add_merge_fuse(spider, "merge_fuse_main_and_pedicel", merged_p_a, pedicel)
    legs = build_legs(spider, fused_pa_p)
    pedipalps = build_pedipalps(spider, fused_pa_p, legs)
    fused = add_merge_fuse(
        spider,
        "merge_fuse_main_legs_pedipalps",
        fused_pa_p,
        legs,
        pedipalps,
    )
    recalculated = add_recalculate_normal(spider, "recalculate_normals", fused)
    _add_subdivide(spider, "debug_subdivision", recalculated, depth=3)
    combined = _add_combine_joint_limits(spider, "combine_joint_limits", recalculated, legs, pedipalps)
    output = add_output(spider, "OUTPUT_SPIDER", combined)

    output.setDisplayFlag(True)
    output.setRenderFlag(True)
    spider.layoutChildren()
    return spider


def _add_spider(parent: hou.OpNode, name: str = "spider") -> hou.SopNode:
    return add_reloadable_subnet(parent, name)


def _add_subdivide(
    parent: hou.OpNode,
    name: str,
    p_input: hou.SopNode,
    depth: int = 1,
) -> hou.SopNode:
    subdivide = parent.createNode("subdivide", name)
    subdivide.setInput(0, p_input)
    subdivide.parm("iterations").set(depth)
    return subdivide


def _add_combine_joint_limits(
    parent: hou.OpNode,
    name: str,
    base_geo: hou.SopNode,
    *limit_sources: hou.SopNode,
) -> hou.SopNode:
    node = sopify(parent, base_geo, combine_joint_limits)
    for i, src in enumerate(limit_sources, 1):
        node.setInput(i, src)
    return node


def combine_joint_limits(node: hou.SopNode) -> None:
    geo = node.geometry()
    combined: dict[str, Any] = {}
    for idx in range(1, len(node.inputs())):
        in_geo = node.inputGeometry(idx)
        if in_geo and in_geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS):
            combined.update(in_geo.dictAttribValue(GlobalAttrib.JOINT_LIMITS))
    if combined:
        attrib = geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS) or geo.addAttrib(
            hou.attribType.Global, GlobalAttrib.JOINT_LIMITS, combined
        )
        geo.setGlobalAttribValue(attrib, combined)

