from dataclasses import dataclass
from typing import Self, Callable


@dataclass
class LimbAttributes:
    """Limb attributes and point ID generator functions.

    All attribute functions take 3 arguments: (segment, loop_index, corner_index)
    where corner_index: 1: left_bottom, 2: right_bottom, 3: right_upper, 4: left_upper.
    """
    segment_region: str
    membrane_region: str
    attribute_edge: Callable[[int, int, int], str]
    attribute_support: Callable[[int, int, int], str]
    attribute_inset: Callable[[int, int, int], str]
    attribute_mid: Callable[[int, int, int], str]
    attribute_membrane: Callable[[int, int | str, int], str]


@dataclass
class LimbParam:
    socket_size: tuple[float, float]

    coxa_length: float
    length_ratios: tuple[float, ...] | list[float]

    segment_sections: tuple[tuple[tuple[float, float, float], ...], ...]

    yaw_flex_specs: tuple[tuple[float, float], ...]
    joint_clearance_limits: tuple[float, float, float]

    spine_ratio: float
    support_loop_ratio: float
    tarsus_wedge_angle: float

    def __post_init__(self) -> None:
        if not (len(self.length_ratios) == len(self.yaw_flex_specs) == len(self.segment_sections) - 1):
            raise ValueError("One length ratio and yaw/flex spec are required per post-coxa segment")
        if self.coxa_length <= 0 or self.support_loop_ratio <= 0:
            raise ValueError("Coxa length and support loop ratio must be positive")
        if any(size <= 0 for size in self.socket_size) or any(ratio <= 0 for ratio in self.length_ratios):
            raise ValueError("Socket dimensions and segment length ratios must be positive")

        segment_sections = []
        for sections in self.segment_sections:
            sections = sorted(sections, key=lambda section: section[0])

            if not sections or any(not 0 <= section[0] <= 1 for section in sections):
                raise ValueError("Each segment needs sections with positions between 0 and 1")
            if any(section[1] <= 0 or section[2] <= 0 for section in sections):
                raise ValueError("Section width and height ratios must be positive")

            if sections[0][0] > 1e-5:
                sections.insert(0, (0.0, *sections[0][1:]))
            if sections[-1][0] < 1 - 1e-5:
                sections.append((1.0, *sections[-1][1:]))

            for i in range(len(sections) - 1):
                if sections[i + 1][0] - sections[i][0] <= 1e-5:
                    raise ValueError(f"Duplicate section position detected at {sections[i][0]:.5f}")

            segment_sections.append(tuple(sections))

        self.segment_sections = tuple(segment_sections)

    @classmethod
    def from_specs(
        cls,
        socket_size: tuple[float, float],
        coxa_length: float,
        length_ratios: tuple[float, ...] | list[float],
        max_segment_yaws: tuple[float, ...] | list[float],
        min_segment_flexes: tuple[float, ...] | list[float],
        segment_sections: tuple[tuple[tuple[float, float, float], ...], ...],
        joint_clearance_limits: tuple[float, float, float],
        spine_ratio: float,
        support_loop_ratio: float,
        tarsus_wedge_angle: float,
    ) -> Self:
        if len(max_segment_yaws) != len(min_segment_flexes) or len(length_ratios) != len(max_segment_yaws):
            raise ValueError("Length ratios, yaw angles, and flex angles must have equal lengths")
        segment_specs = tuple(zip(max_segment_yaws, min_segment_flexes))
        return cls(
            socket_size=socket_size,
            coxa_length=coxa_length,
            length_ratios=length_ratios,
            yaw_flex_specs=segment_specs,
            segment_sections=segment_sections,
            joint_clearance_limits=joint_clearance_limits,
            spine_ratio=spine_ratio,
            support_loop_ratio=support_loop_ratio,
            tarsus_wedge_angle=tarsus_wedge_angle,
        )
