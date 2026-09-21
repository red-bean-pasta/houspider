import hou

from houkit.noder import add_fuse, add_merge, add_output, add_reload_button, sopify
from . import topology


def build(
    parent: hou.OpNode,
    spider: hou.OpNode,
) -> hou.OpNode:
    skeleton = _add_skeleton(parent)
    skeleton.setInput(0, spider)

    source = _add_import(skeleton, "in_spider")
    body_skel = sopify(skeleton, source, topology.build_body_skeleton)
    legs_skel = sopify(skeleton, source, topology.build_leg_skeletons)
    pedipalps_skel = sopify(skeleton, source, topology.build_pedipalps_skeleton)

    merged = add_merge(skeleton, "merge_skeletons", body_skel, legs_skel, pedipalps_skel)
    fused = add_fuse(skeleton, "fuse_root", merged)

    rig_doctor = _add_rig_doctor(skeleton, "rig_doctor", fused)
    add_output(skeleton, "OUT_SKELETON", rig_doctor)

    skeleton.layoutChildren()
    return skeleton


def _add_skeleton(parent: hou.OpNode) -> hou.OpNode:
    skeleton = parent.node("skeleton")
    if not skeleton:
        skeleton = parent.createNode("geo", "skeleton")
        for child in skeleton.children():
            child.destroy()
        add_reload_button(skeleton)
    return skeleton


def _add_import(
    parent: hou.OpNode,
    name: str,
    target_path: str = '`opinputpath("..", 0)`',
) -> hou.SopNode:
    om = parent.createNode("object_merge", name)
    om.parm("objpath1").set(target_path)
    return om


def _add_rig_doctor(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
) -> hou.SopNode:
    rd = parent.createNode("kinefx::rigdoctor", name)
    rd.setInput(0, input_node)
    rd.parm("inittransforms").set(1)
    rd.parm("reorienttochild").set(1)
    rd.parm("outputparentidx").set(1)
    return rd
