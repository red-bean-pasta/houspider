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
    loop_index: int | str,
    corner_index: int | str,
) -> str:
    """Return point ID for a pedipalp segment point.

    :param side: 1 for right pedipalp, -1 for left pedipalp.
    :param segment_index: 1..6 (1: coxa .. 6: tarsus).
    :param loop_index: 1: start_inset, 2: start, 3: start_support,
                       4: end_support, 5: end, 6: end_inset.
    :param corner_index: 1: left_bottom (-X, -Y), 2: right_bottom (+X, -Y),
                         3: right_upper (+X, +Y), 4: left_upper (-X, +Y).
    """
    return affix_id(ID.PEDIPALPSEGMENT, side, segment_index, loop_index, corner_index)


def pedipalpmembrane(
    side: int | str,
    joint_index: int | str,
    loop_index: int | str,
    corner_index: int | str,
) -> str:
    """Return point ID for a pedipalp joint membrane point.

    :param side: 1 for right pedipalp, -1 for left pedipalp.
    :param joint_index: 1..5 (1: coxa-trochanter .. 5: tibia-tarsus).
    :param loop_index: 1: former_support, 2: middle, 3: latter_support.
    :param corner_index: 1: left_bottom (-X, -Y), 2: right_bottom (+X, -Y),
                         3: right_upper (+X, +Y), 4: left_upper (-X, +Y).
    """
    return affix_id(ID.PEDIPALPMEMBRANE, side, joint_index, loop_index, corner_index)


def pedipalpcoxabuffer(
    side: int | str,
    *identifiers: int | str,
) -> str:
    """Return point ID for a pedipalp coxa buffer point."""
    return affix_id(ID.PEDIPALPSEGMENT, side, 1, "buffer", *identifiers)
