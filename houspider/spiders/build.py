import hou

from houkit.noder import (
    add_fuse,
    add_merge,
    add_recalculate_normal,
    add_reloadable_subnet,
    sopify,
)
from houkit.nodes.sops import add_output
from ..abdomens.build import build as build_abdomen
from ..cephalothoraxes.build import build as build_cephalothorax
from ..legs.build import build as build_legs
from ..pedicels.build import build as build_pedicel
from . import topology


def build(parent: hou.OpNode, name: str = "spider") -> hou.SopNode:
    spider = _add_spider(parent, name)

    cephalothorax = build_cephalothorax(spider)

    abdomen_node = build_abdomen(spider, cephalothorax)

    opened_abdomen = sopify(spider, abdomen_node, topology.open_abdomen_pedicel)
    merged_c_a = add_merge(spider, "merge_cephalothorax_and_abdomen", cephalothorax, opened_abdomen)

    pedicel = build_pedicel(spider, merged_c_a)
    merged_ca_p = add_merge(spider, "merge_main_and_pedicel", merged_c_a, pedicel)
    fused_ca_p = add_fuse(spider, "fuse_main_and_pedicel", merged_ca_p)
    removed_sockets = sopify(spider, fused_ca_p, topology.remove_coxa_sockets)

    legs = build_legs(spider, fused_ca_p)
    merged_all = add_merge(spider, "merge_main_and_legs", removed_sockets, legs)
    fused = add_fuse(spider, "fuse_main_and_legs", merged_all)

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
