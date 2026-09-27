import math
from pathlib import Path

import hou

from houkit.noder import add_fuse, add_merge, add_output, add_reloadable_subnet, sopify
from ..attributes import GlobalAttrib
from . import skinning, topology
from .attributes import LegJoint

# The skeleton design in Houdini is so over-engineered...

def build(
    parent: hou.OpNode,
    name: str = "skeleton",
    input_node: hou.SopNode | None = None,
) -> hou.OpNode:
    skeleton = _add_skeleton(parent, name)
    if input_node is not None:
        skeleton.setInput(0, input_node)
    assert input_node is not None

    source = skeleton.indirectInputs()[0]
    body_skel = sopify(skeleton, source, topology.build_body_skeleton)
    legs_skel = sopify(skeleton, source, topology.build_leg_skeletons)
    pedipalps_skel = sopify(skeleton, source, topology.build_pedipalps_skeleton)

    merged = add_merge(skeleton, "merge_skeletons", body_skel, legs_skel, pedipalps_skel)
    fused = add_fuse(skeleton, "fuse_root", merged)

    rig_doctor = _add_rig_doctor(skeleton, "rig_doctor", fused)
    tagged = sopify(skeleton, rig_doctor, topology.add_ik_tags)

    captured_skin = skinning.capture_skin(skeleton, source)
    character = _add_pack_character(skeleton, "pack_character", captured_skin, tagged)

    multi_ik = _add_multi_ik(skeleton, "multi_ik", character)
    joint_limits = input_node.geometry().attribValue(GlobalAttrib.JOINT_LIMITS)
    multi_ik_constraints = _add_multi_ik_constraints(
        skeleton,
        "multi_ik_constraints",
        multi_ik,
        joint_limits,
    ) # Multi IK ships an internal Multi Bone IK but doesn't expose joint constraints APIs

    scene = _add_scene_add_character(skeleton, "scene_add_character", multi_ik_constraints)
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

    ik.parm("solver").set(1)
    ik.parm("segments").set("leg_*")

    return ik


def _add_multi_ik_constraints(
    parent: hou.OpNode,
    name: str,
    input_node: hou.SopNode,
    joint_limits: dict[str, tuple[float, ...]],
) -> hou.SopNode:
    constraints = parent.createNode("apex::autorigcomponent::3.0", name)
    constraints.parm("inputguidename").set("Guides.skel")
    constraints.setInput(0, input_node)
    constraints.parm("componentsource").set("__SNIPPET__")
    constraints.parm("snippet").set(
        (
            Path(__file__).resolve().parents[2]
            / "apexcomponent"
            / "multi_ik_constraints.apex"
        ).read_text()
    )
    constraints.hdaModule().onComponentSourceUpdated({
        "node": constraints,
        "parm": constraints.parm("componentsource"),
    })

    min_flex = joint_limits["min_flex_angles"]
    max_flex = joint_limits["max_flex_angles"]
    min_yaw = joint_limits["min_yaw_angles"]
    max_yaw = joint_limits["max_yaw_angles"]
    assert len(min_flex) == len(max_flex) == len(min_yaw) == len(max_yaw), "Joint-limit arrays must have equal lengths."
    joint_limit_specs = tuple(zip(min_flex, max_flex, min_yaw, max_yaw))
    assert len(joint_limit_specs) == len(LegJoint) - 1, "Expected one constraint for each leg joint through the tarsus."

    count = len(joint_limit_specs)
    constraints.parm("limits").set(count)
    for index, (lo_flex, hi_flex, lo_yaw, hi_yaw) in enumerate(joint_limit_specs, 1):
        constraints.parmTuple(f"lower{index}").set((
            math.radians(lo_flex - 180.0),
            math.radians(lo_yaw),
            -math.pi,
        ))
        constraints.parmTuple(f"upper{index}").set((
            math.radians(hi_flex - 180.0),
            math.radians(hi_yaw),
            math.pi,
        ))
        constraints.parmTuple(f"restangle{index}").set((0.0, 0.0, 0.0))

    return constraints


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
