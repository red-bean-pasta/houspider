import hou

from .skeletons.builder import build as build_skeleton


def build(
    spider: hou.OpNode,
    spider_geo: hou.SopNode,
) -> hou.SopNode:
    return build_skeleton(spider, spider_geo)
