import hou

from houkit.noder import add_reload_button
from houkit.parameterizer import promote_subnets, promote_controls
from houkit.parameterizings.operator import add_folder

from . import builds


def build() -> hou.OpNode:
    root = _get_root()
    spider_node = _add_geo(root, "spider")

    geometry = builds.build_spider(spider_node, name="geometry")

    skel = builds.build_skeleton(
        spider_node,
        name="skeleton",
        input_node=geometry,
    )

    _propagate_parameters(spider_node)

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


def _propagate_parameters(parent: hou.OpNode) -> None:
    add_folder(parent, "build")
    promote_subnets(parent, depth=None, dest_group="Build")

    add_folder(parent, "advanced")
    promote_controls(parent, depth=None, dest_group="Advanced",)
