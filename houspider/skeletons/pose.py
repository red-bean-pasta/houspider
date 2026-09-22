import hou
from houkit.attributings.querier import unique_points_by_attrib

from .attributes import LegJoint, leg_joint_name


def add_leg_rig_pose(
    parent: hou.OpNode,
    input_node: hou.SopNode,
) -> hou.SopNode:
    pose = parent.createNode("kinefx::rigpose", "rig_pose")
    pose.setInput(0, input_node)

    input_node.cook(force=True)
    rotations = _get_leg_trochanter_rotations(input_node.geometry())
    pose.parm("transformations").set(len(rotations))
    for index, (name, rotation) in enumerate(rotations):
        pose.parm(f"group{index}").set(f"@name={name}")
        pose.parm(f"xOrd{index}").set("srt")
        pose.parm(f"rOrd{index}").set("xyz")
        pose.parmTuple(f"r{index}").set(tuple(rotation))
    return pose


def _get_leg_trochanter_rotations(
    geo: hou.Geometry,
) -> list[tuple[str, hou.Vector3]]:
    points = unique_points_by_attrib(geo, "name")
    rotations: list[tuple[str, hou.Vector3]] = []
    for is_right in (True, False):
        for leg_index in range(1, 5):
            coxa_name = leg_joint_name(is_right, leg_index, LegJoint.COXA)
            trochanter_name = leg_joint_name(is_right, leg_index, LegJoint.TROCHANTER)
            femur_name = leg_joint_name(is_right, leg_index, LegJoint.FEMUR)
            coxa = points[coxa_name]
            trochanter = points[trochanter_name]
            femur = points[femur_name]
            rotations.append(
                (
                    trochanter_name,
                    _get_alignment_rotation(coxa, trochanter, femur),
                )
            )
    return rotations


def _get_alignment_rotation(
    coxa: hou.Point,
    trochanter: hou.Point,
    femur: hou.Point,
) -> hou.Vector3:
    trochanter_transform = hou.Matrix4(
        hou.Matrix3(trochanter.attribValue("transform"))
    )
    trochanter_transform_inverse = trochanter_transform.inverted()
    current_direction = (femur.position() - trochanter.position()).normalized()
    target_direction = (trochanter.position() - coxa.position()).normalized()
    current_local = current_direction.multiplyAsDir(trochanter_transform_inverse)
    target_local = target_direction.multiplyAsDir(trochanter_transform_inverse)

    rotation = hou.Quaternion()
    rotation.setToVectors(current_local, target_local)
    rotation_matrix = hou.Matrix4(rotation.extractRotationMatrix3())
    return rotation_matrix.extractRotates("srt", "xyz")
