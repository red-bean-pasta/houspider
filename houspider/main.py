import hou

from houkit.noder import add_reload_button
from . import skeleton, spider


def build() -> hou.OpNode:
    root = _get_root()
    spider_node = _add_geo(root, "spider")
    geometry = spider.build(spider_node, name="geometry")
    skel = skeleton.build(spider_node, name="skeleton")
    skel.setInput(0, geometry)

    spider_node.layoutChildren()
    root.layoutChildren()
    return spider_node


def _get_root() -> hou.OpNode:
    obj = hou.node("/obj")
    assert obj is not None, "Expected /obj node"
    return obj


def _add_geo(parent: hou.OpNode, name: str) -> hou.OpNode:
    node = parent.node(name)
    if not node:
        node = parent.createNode("geo", name)
        for child in node.children():
            child.destroy()
        add_reload_button(node)
    return node
