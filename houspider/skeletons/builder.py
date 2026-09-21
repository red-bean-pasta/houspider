import hou

from houkit.noder import add_fuse, add_merge, add_output, add_reloadable_subnet, sopify
from . import topology


def build(
    spider: hou.OpNode,
    spider_geo: hou.SopNode,
) -> hou.SopNode:
    skeleton = add_reloadable_subnet(spider, "skeleton")
    skeleton.setInput(0, spider_geo)

    source = skeleton.indirectInputs()[0]
    body_skel = sopify(skeleton, source, topology.build_body_skeleton)
    legs_skel = sopify(skeleton, source, topology.build_leg_skeletons)
    pedipalps_skel = sopify(skeleton, source, topology.build_pedipalps_skeleton)

    merged = add_merge(skeleton, "merge_skeletons", body_skel, legs_skel, pedipalps_skel)
    fused = add_fuse(skeleton, "fuse_root", merged)

    rig_doctor = _add_rig_doctor(skeleton, "rig_doctor", fused)
    add_output(skeleton, "OUT_SKELETON", rig_doctor)

    skeleton.layoutChildren()
    return skeleton


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
