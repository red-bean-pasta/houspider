from enum import StrEnum, auto

import hou

from ..attributes import LegSegment
from ..helper import affix_id


class Region(StrEnum):
    LEGSEGMENT = auto()
    LEGMEMBRANE = auto()


class ID(StrEnum):
    LEGSEGMENT = auto()
    LEGMEMBRANE = auto()


def legsegment(
    leg_index: int | str,
    segment_index: int | str,
    loop_index: int | str,
    corner_index: int | str,
) -> str:
    """Return point ID for a leg segment point.

    :param leg_index: 1..4 for right legs, -1..-4 for left legs.
    :param segment_index: 1..7 (1: coxa .. 7: tarsus).
    :param loop_index: 1: start_inset, 2: start, 3: start_support,
                       4: end_support, 5: end, 6: end_inset.
    :param corner_index: 1: left_bottom (-X, -Y), 2: right_bottom (+X, -Y),
                         3: right_upper (+X, +Y), 4: left_upper (-X, +Y).
    """
    return affix_id(ID.LEGSEGMENT, leg_index, segment_index, loop_index, corner_index)


def legmembrane(
    leg_index: int | str,
    joint_index: int | str,
    loop_index: int | str,
    corner_index: int | str,
) -> str:
    """Return point ID for a leg joint membrane point.

    :param leg_index: 1..4 for right legs, -1..-4 for left legs.
    :param joint_index: 1..6 (1: coxa-trochanter .. 6: metatarsus-tarsus).
    :param loop_index: 1: former_support, 2: middle, 3: latter_support.
    :param corner_index: 1: left_bottom (-X, -Y), 2: right_bottom (+X, -Y),
                         3: right_upper (+X, +Y), 4: left_upper (-X, +Y).
    """
    return affix_id(ID.LEGMEMBRANE, leg_index, joint_index, loop_index, corner_index)


def get_segment_sections(
    node: hou.OpNode,
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    all_sections = []
    for name in LegSegment:
        sections_parm = node.parm(f"{name}_sections")
        num_sections = sections_parm.eval()
        sections = []
        for i in range(num_sections):
            parm_tuple = node.parmTuple(f"{name}_section{i + 1}")
            sections.append(tuple(parm_tuple.eval()))
        all_sections.append(tuple(sections))
    return tuple(all_sections)
