import hou

from houkit.noder import add_fuse, add_merge, add_output, add_reloadable_subnet, sopify
from . import skinning, topology

# The skeleton design in Houdini is so over-engineered...

def build(
    parent: hou.OpNode,
    name: str = "skeleton",
    input_node: hou.SopNode | None = None,
) -> hou.OpNode:
    skeleton = _add_skeleton(parent, name)
    if input_node is not None:
        skeleton.setInput(0, input_node)

    source = skeleton.indirectInputs()[0]
    body_skel = sopify(skeleton, source, topology.build_body_skeleton)
    legs_skel = sopify(skeleton, source, topology.build_leg_skeletons)
    pedipalps_skel = sopify(skeleton, source, topology.build_pedipalps_skeleton)

    merged = add_merge(skeleton, "merge_skeletons", body_skel, legs_skel, pedipalps_skel)
    fused = add_fuse(skeleton, "fuse_root", merged)

    rig_doctor = _add_rig_doctor(skeleton, "rig_doctor", fused)
    tagged = sopify(skeleton, rig_doctor, topology.add_ik_tags)
    rig_stash = _add_rig_stash(skeleton, "rig_stash", tagged)

    captured_skin = skinning.capture_skin(skeleton, source)
    character = _add_pack_character(skeleton, "pack_character", captured_skin, rig_stash)
    multi_ik = _add_multi_ik(skeleton, "multi_ik", character)
    scene = _add_scene_add_character(skeleton, "scene_add_character", multi_ik)
    animator = _add_scene_animate(skeleton, "scene_animate", scene)

    output = add_output(skeleton, "OUT_EVALUATED", animator)
    output.setInput(0, animator, 1)

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


def _add_rig_stash(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
) -> hou.SopNode:
    rs = parent.createNode("kinefx::rigstashpose", name)
    rs.setInput(0, input_node)
    return rs


def _add_pack_character(
    parent: hou.OpNode,
    name: str,
    skin: hou.SopNode,
    skeleton: hou.SopNode,
) -> hou.SopNode:
    pack = parent.createNode("apex::packcharacter", name)
    pack.setInput(1, skin)
    pack.setInput(2, skeleton)
    pack.setInput(3, skeleton)
    pack.parm("addbaserig").set(1)
    pack.parm("tpromotegroup").set("root")
    pack.parm("rpromotegroup").set("")
    pack.parm("spromotegroup").set("")
    return pack


def _add_multi_ik(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
) -> hou.SopNode:
    ik = parent.createNode("apex::autorigcomponent::3.0", name)
    ik.parm("inputguidename").set("Guides.skel") # To supress OnInputChanged callback error during hython builds
    ik.setInput(0, input_node)

    ik.parm("componentsource").set("multiik")
    # HOM parameter changes do not run the component source callback.
    ik.hdaModule().onComponentSourceUpdated({"node": ik, "parm": ik.parm("componentsource")})

    ik.parm("segments").set("leg_*")
    ik.parm("driven").set("%tag(bind)")

    return ik


def _add_scene_add_character(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
) -> hou.SopNode:
    scene = parent.createNode("apex::sceneaddcharacter", name)
    scene.setInput(1, input_node)
    scene.parm("charactername").set("spider")
    return scene


def _add_scene_animate(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
) -> hou.SopNode:
    animator = parent.createNode("apex::sceneanimate", name)
    animator.setInput(0, input_node)
    return animator
