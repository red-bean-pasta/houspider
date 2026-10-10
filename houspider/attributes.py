from enum import StrEnum, auto


class GlobalAttrib(StrEnum):
    JOINT_LIMITS = auto()


class JointLimitKey(StrEnum):
    MIN_FLEX_ANGLES = "min_flex_angles"
    MAX_FLEX_ANGLES = "max_flex_angles"
    MIN_YAW_ANGLES = "min_yaw_angles"
    MAX_YAW_ANGLES = "max_yaw_angles"
    REST_FLEX_ANGLES = "rest_flex_angles"
    REST_FLEX_RATIOS = "rest_flex_ratios"


class BodyJoint(StrEnum):
    ROOT = "root"
    PEDICEL = "pedicel"
    ABDOMEN = "abdomen"


class LegSegment(StrEnum):
    COXA = "coxa"
    TROCHANTER = "trochanter"
    FEMUR = "femur"
    PATELLA = "patella"
    TIBIA = "tibia"
    METATARSUS = "metatarsus"
    TARSUS = "tarsus"


class PedipalpSegment(StrEnum):
    COXA = "coxa"
    TROCHANTER = "trochanter"
    FEMUR = "femur"
    PATELLA = "patella"
    TIBIA = "tibia"
    TARSUS = "tarsus"


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