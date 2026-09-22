import hou

from .skeletons.builder import build as build_skeleton


def build(
    parent: hou.OpNode,
    name: str = "skeleton",
) -> hou.OpNode:
    return build_skeleton(parent, name=name)
