from enum import StrEnum, auto

from ..helper import affix_id


class Region(StrEnum):
    PEDIPALPSEGMENT = auto()
    PEDIPALPMEMBRANE = auto()


class ID(StrEnum):
    PEDIPALPSEGMENT = auto()
    PEDIPALPMEMBRANE = auto()


def pedipalpsegment(
    side: int | str,
    segment_index: int | str,
    *identifiers: int | str,
) -> str:
    """Return point ID for a pedipalp segment point.

    :param side: 1 for right, -1 for left.
    :param segment_index: 1..6 (1: coxa .. 6: tarsus).
    """
    return affix_id(ID.PEDIPALPSEGMENT, side, segment_index, *identifiers)


def pedipalpsegmentedge(
    side: int | str,
    segment_index: int | str,
    direction: int | str,
    corner_index: int | str,
) -> str:
    return pedipalpsegment(side, segment_index, "edge", direction, corner_index)


def pedipalpsegmentsupport(
    side: int | str,
    segment_index: int | str,
    direction: int | str,
    corner_index: int | str,
) -> str:
    return pedipalpsegment(side, segment_index, "support", direction, corner_index)


def pedipalpsegmentinset(
    side: int | str,
    segment_index: int | str,
    direction: int | str,
    corner_index: int | str,
) -> str:
    return pedipalpsegment(side, segment_index, "inset", direction, corner_index)


def pedipalpsegmentmid(
    side: int | str,
    segment_index: int | str,
    mid_index: int | str,
    corner_index: int | str,
) -> str:
    return pedipalpsegment(side, segment_index, "mid", mid_index, corner_index)


def pedipalpcoxabuffer(
    side: int | str,
    *identifiers: int | str,
) -> str:
    return pedipalpsegment(side, 1, "buffer", *identifiers)


def pedipalpmembrane(
    side: int | str,
    joint_index: int | str,
    loop_index: int | str,
    corner_index: int | str,
) -> str:
    """Return point ID for a pedipalp joint membrane point.

    :param side: 1 for right, -1 for left.
    :param joint_index: 1..5 (1: coxa-trochanter .. 5: tibia-tarsus).
    :param loop_index: 1: former_support, "mid": middle, -1: latter_support.
    :param corner_index: 1: left_bottom (-X, -Y), 2: right_bottom (+X, -Y),
                         3: right_upper (+X, +Y), 4: left_upper (-X, +Y).
    """
    return affix_id(ID.PEDIPALPMEMBRANE, side, joint_index, loop_index, corner_index)


def pedipalpmembranemid(
    side: int | str,
    joint_index: int | str,
    corner_index: int | str,
) -> str:
    return pedipalpmembrane(side, joint_index, "mid", corner_index)
