from dataclasses import dataclass
from typing import Any, Sequence, Self

import hou

from .attributes import GlobalAttrib, JointLimitKey


@dataclass(frozen=True)
class JointLimits:
    min_flex: tuple[float, ...]
    max_flex: tuple[float, ...]
    min_yaw: tuple[float, ...]
    max_yaw: tuple[float, ...]
    rest_ratios: tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.min_flex)
        if not (
            len(self.max_flex) == n
            and len(self.min_yaw) == n
            and len(self.max_yaw) == n
            and len(self.rest_ratios) == n
        ):
            raise ValueError(
                f"Mismatched joint limit lengths: min_flex={len(self.min_flex)}, "
                f"max_flex={len(self.max_flex)}, min_yaw={len(self.min_yaw)}, "
                f"max_yaw={len(self.max_yaw)}, rest_ratios={len(self.rest_ratios)}"
            )
        for lo, hi in zip(self.min_flex, self.max_flex):
            if lo > hi:
                raise ValueError(f"min_flex ({lo}) cannot exceed max_flex ({hi})")
        for lo, hi in zip(self.min_yaw, self.max_yaw):
            if lo > hi:
                raise ValueError(f"min_yaw ({lo}) cannot exceed max_yaw ({hi})")
        for r in self.rest_ratios:
            if not (0.0 <= r <= 1.0):
                raise ValueError(f"rest_ratio ({r}) must be in range [0.0, 1.0]")

    @property
    def rest_flex(self) -> tuple[float, ...]:
        return tuple(
            lo + r * (hi - lo)
            for lo, hi, r in zip(self.min_flex, self.max_flex, self.rest_ratios)
        )

    def select(self, indices: Sequence[int], rest_ratios: Sequence[float]) -> Self:
        return JointLimits(
            min_flex=tuple(self.min_flex[i] for i in indices),
            max_flex=tuple(self.max_flex[i] for i in indices),
            min_yaw=tuple(self.min_yaw[i] for i in indices),
            max_yaw=tuple(self.max_yaw[i] for i in indices),
            rest_ratios=tuple(rest_ratios),
        )

    def to_dict(self) -> dict[str, tuple[float, ...]]:
        return {
            JointLimitKey.MIN_FLEX_ANGLES.value: self.min_flex,
            JointLimitKey.MAX_FLEX_ANGLES.value: self.max_flex,
            JointLimitKey.MIN_YAW_ANGLES.value: self.min_yaw,
            JointLimitKey.MAX_YAW_ANGLES.value: self.max_yaw,
            JointLimitKey.REST_FLEX_RATIOS.value: self.rest_ratios,
            JointLimitKey.REST_FLEX_ANGLES.value: self.rest_flex,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        min_flex = tuple(data[JointLimitKey.MIN_FLEX_ANGLES.value])
        max_flex = tuple(data[JointLimitKey.MAX_FLEX_ANGLES.value])
        min_yaw = tuple(data[JointLimitKey.MIN_YAW_ANGLES.value])
        max_yaw = tuple(data[JointLimitKey.MAX_YAW_ANGLES.value])
        rest_ratios = tuple(
            data.get(
                JointLimitKey.REST_FLEX_RATIOS.value,
                (0.5,) * len(min_flex),
            )
        )
        return cls(
            min_flex=min_flex,
            max_flex=max_flex,
            min_yaw=min_yaw,
            max_yaw=max_yaw,
            rest_ratios=rest_ratios,
        )

    @classmethod
    def from_geometry(cls, geo: hou.Geometry, pattern: str) -> Self:
        attrib = geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS)
        assert attrib, f"Global attribute '{GlobalAttrib.JOINT_LIMITS}' not found on geometry"
        all_limits = geo.dictAttribValue(attrib)
        data = all_limits.get(pattern)
        assert data, f"Pattern '{pattern}' not found in '{GlobalAttrib.JOINT_LIMITS}' dict"
        return cls.from_dict(data)

    def write_to_geometry(self, geo: hou.Geometry, pattern: str) -> None:
        attrib = geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS)
        limits_dict = dict(geo.dictAttribValue(attrib)) if attrib else {}
        limits_dict[pattern] = self.to_dict()
        if not attrib:
            geo.addAttrib(hou.attribType.Global, GlobalAttrib.JOINT_LIMITS, limits_dict)
        geo.setGlobalAttribValue(GlobalAttrib.JOINT_LIMITS, limits_dict)
