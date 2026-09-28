from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Self

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


@dataclass
class LegParam:
    coxa_width_length: tuple[float, float]
    length_ratios: tuple[float, ...] | list[float]
    yaw_flex_specs: tuple[tuple[float, float], ...]

    tarsus_wedge_angle: float = 45.0

    coxa_trochanter_height_ratio: float = 0.63
    other_segment_height_ratio: float = 1.15
    spine_ratio: float = 0.5
    shrink_ratios: tuple[float, float] = (0.95, 0.875)
    support_loop_ratio: float = 0.015

    minimum_membrane: tuple[float, float] = (1.0, 5.0)

    def __post_init__(self) -> None:
        assert len(self.length_ratios) == len(self.yaw_flex_specs), (
            f"Length mismatch: length_ratios ({len(self.length_ratios)}) != yaw_flex_specs ({len(self.yaw_flex_specs)})"
        )

    @classmethod
    def from_specs(
        cls,
        coxa_width_length: tuple[float, float],
        length_ratios: tuple[float, ...] | list[float],
        max_segment_yaws: tuple[float, ...] | list[float],
        min_segment_flexes: tuple[float, ...] | list[float],
        **kwargs,
    ) -> Self:
        assert len(max_segment_yaws) == len(min_segment_flexes), (
            f"Spec mismatch: max_segment_yaws ({len(max_segment_yaws)}) != min_segment_flexes ({len(min_segment_flexes)})"
        )
        assert len(length_ratios) == len(max_segment_yaws), (
            f"Length mismatch: length_ratios ({len(length_ratios)}) != max_segment_yaws ({len(max_segment_yaws)})"
        )
        segment_specs = tuple(zip(max_segment_yaws, min_segment_flexes))
        return cls(
            coxa_width_length=coxa_width_length,
            length_ratios=length_ratios,
            yaw_flex_specs=segment_specs,
            **kwargs,
        )
