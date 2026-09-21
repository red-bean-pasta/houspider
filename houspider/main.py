import hou

from . import skeleton, spider


def build() -> hou.OpNode:
    root = _get_root()
    spider_node = spider.build(root)
    skeleton.build(root, spider_node)
    root.layoutChildren()
    return spider_node


def _get_root() -> hou.OpNode:
    obj = hou.node("/obj")
    assert obj is not None, "Expected /obj node"
    return obj
