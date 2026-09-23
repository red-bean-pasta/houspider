import hou
from houkit.skeleton import get_named_point_alignment_rotation
from houkit.noder import add_rig_pose

from .attributes import LegJoint, leg_joint_name, body_joint_name, BodyJoint, pedipalp_joint_name, PedipalpJoint





# Legacy
def add_align_rig_pose(
    parent: hou.OpNode,
    input_node: hou.SopNode,
) -> hou.SopNode:
    geo = input_node.geometry()
    return add_rig_pose(
        parent,
        input_node,
        _get_pedicel_align_rotations(geo),
        *_get_leg_align_rotations(geo),
        *_get_pedipalp_align_rotations(geo),
    )

def _get_pedicel_align_rotations(
    geo: hou.Geometry,
) -> tuple[str, hou.Vector3]:
    pedicel_name = body_joint_name(BodyJoint.PEDICEL)
    rotation = get_named_point_alignment_rotation(
        geo,
        body_joint_name(BodyJoint.ROOT),
        pedicel_name,
        body_joint_name(BodyJoint.ABDOMEN),
    )
    return pedicel_name, rotation

def _get_pedipalp_align_rotations(
    geo: hou.Geometry,
) -> list[tuple[str, hou.Vector3]]:
    rotations: list[tuple[str, hou.Vector3]] = []
    for is_right in (True, False):
        trochanter_name = pedipalp_joint_name(is_right, PedipalpJoint.TROCHANTER)
        rotation = get_named_point_alignment_rotation(
            geo,
            pedipalp_joint_name(is_right, PedipalpJoint.COXA),
            trochanter_name,
            pedipalp_joint_name(is_right, PedipalpJoint.FEMUR),
        )
        rotations.append((trochanter_name, rotation))
    return rotations

def _get_leg_align_rotations(
    geo: hou.Geometry,
) -> list[tuple[str, hou.Vector3]]:
    rotations: list[tuple[str, hou.Vector3]] = []
    for is_right in (True, False):
        for leg_index in range(1, 5):
            trochanter_name = leg_joint_name(is_right, leg_index, LegJoint.TROCHANTER)
            rotation = get_named_point_alignment_rotation(
                geo,
                leg_joint_name(is_right, leg_index, LegJoint.COXA),
                trochanter_name,
                leg_joint_name(is_right, leg_index, LegJoint.FEMUR),
            )
            rotations.append((trochanter_name, rotation))
    return rotations
