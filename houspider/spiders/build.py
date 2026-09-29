import hou

from houkit.noder import (
    add_merge,
    add_merge_fuse,
    add_recalculate_normal,
    add_reloadable_subnet,
)
from houkit.nodes.sops import add_output
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
    output = add_output(spider, "OUTPUT_SPIDER", recalculated)

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
