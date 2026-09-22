import hou

from .spiders.builder import build as build_spider


def build(parent: hou.OpNode, name: str = "spider") -> hou.SopNode:
    return build_spider(parent, name=name)
