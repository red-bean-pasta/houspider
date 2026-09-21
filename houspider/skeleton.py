import hou

from .skeletons.builder import build as build_skeleton


def build(
    parent: hou.OpNode,
    spider: hou.OpNode,
) -> hou.OpNode:
    return build_skeleton(parent, spider)
