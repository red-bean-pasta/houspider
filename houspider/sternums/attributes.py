from enum import StrEnum, auto

from houspider.helper import affix_id


class ID(StrEnum):
    STERNUMRIM = auto()
    STERNUMRIMMIDDLE = auto()
    STERNUMSPINE = auto()


def sternumrim(*i: int | str) -> str:
    return affix_id(ID.STERNUMRIM, *i)


def sternumrimmiddle(*i: int | str) -> str:
    return affix_id(ID.STERNUMRIMMIDDLE, *i)


def sternumspine(*i: int | str) -> str:
    return affix_id(ID.STERNUMSPINE, *i)


def outer_rim_ids() -> tuple[str, str]:
    return ID.STERNUMRIM, ID.STERNUMRIMMIDDLE
