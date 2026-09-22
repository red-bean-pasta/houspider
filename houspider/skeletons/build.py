import hou

from houkit.noder import add_fuse, add_merge, add_output, add_reloadable_subnet, sopify
from . import pose, skinning, topology


def build(
    parent: hou.OpNode,
    name: str = "skeleton",
    input_node: hou.SopNode | None = None,
    parameter_node: hou.SopNode | None = None,
) -> hou.OpNode:
    skeleton = _add_skeleton(parent, name)
    if input_node is not None:
        skeleton.setInput(0, input_node)
    if parameter_node is not None:
        skeleton.setInput(1, parameter_node)

    source = skeleton.indirectInputs()[0]
    body_skel = sopify(skeleton, source, topology.build_body_skeleton)
    legs_skel = sopify(skeleton, source, topology.build_leg_skeletons)
    pedipalps_skel = sopify(skeleton, source, topology.build_pedipalps_skeleton)

    merged = add_merge(skeleton, "merge_skeletons", body_skel, legs_skel, pedipalps_skel)
    fused = add_fuse(skeleton, "fuse_root", merged)

    rig_doctor = _add_rig_doctor(skeleton, "rig_doctor", fused)
    rig_pose = pose.add_leg_rig_pose(skeleton, rig_doctor)
    add_output(skeleton, "OUT_SKELETON", rig_pose)

    captured_skin = skinning.capture_skin(skeleton, source)
    deformed_skin = skinning.deform_skin(skeleton, captured_skin, rig_doctor, rig_pose)
    add_output(skeleton, "OUT_SKIN", deformed_skin)

    skeleton.layoutChildren()
    return skeleton


def _add_skeleton(parent: hou.OpNode, name: str = "skeleton") -> hou.OpNode:
    return add_reloadable_subnet(parent, name)


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
