from enum import StrEnum


class BodyJoint(StrEnum):
    ROOT = "root"
    PEDICEL = "pedicel"
    ABDOMEN = "abdomen"


class LegJoint(StrEnum):
    COXA = "coxa"
    TROCHANTER = "trochanter"
    FEMUR = "femur"
    PATELLA = "patella"
    TIBIA = "tibia"
    METATARSUS = "metatarsus"
    TARSUS = "tarsus"
    TIP = "tip"


class PedipalpJoint(StrEnum):
    COXA = "coxa"
    TROCHANTER = "trochanter"
    FEMUR = "femur"
    PATELLA = "patella"
    TIBIA = "tibia"
    TARSUS = "tarsus"
    TIP = "tip"


def body_joint_name(joint: BodyJoint | str) -> str:
    return str(joint)


def leg_joint_name(
    is_right: bool,
    leg_index: int,
    joint: LegJoint | str,
) -> str:
    return f"leg_{_side_bool_to_str(is_right)}{leg_index}_{joint}"


def pedipalp_joint_name(
    is_right: bool,
    joint: PedipalpJoint | str,
) -> str:
    return f"pedipalp_{_side_bool_to_str(is_right)}_{joint}"


def _side_bool_to_str(is_right: bool) -> str:
    return "R" if is_right else "L"
