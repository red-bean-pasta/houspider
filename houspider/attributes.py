from enum import StrEnum, auto


class GlobalAttrib(StrEnum):
    JOINT_LIMITS = auto()


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