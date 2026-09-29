from enum import StrEnum, auto

from ..helper import affix_id


class ID(StrEnum):
    PROSOMAPEDICELUPPER = auto()
    PROSOMAPEDICELLOWER = auto()
    PROSOMAPEDICELRIGHT = auto()
    PROSOMAPEDICELLEFT = auto()


def prosomapedicelupper(*i: int | str) -> str:
    return affix_id(ID.PROSOMAPEDICELUPPER, *i)


def prosomapedicellower(*i: int | str) -> str:
    return affix_id(ID.PROSOMAPEDICELLOWER, *i)


def prosomapedicelright(*i: int | str) -> str:
    return affix_id(ID.PROSOMAPEDICELRIGHT, *i)


def prosomapedicelleft(*i: int | str) -> str:
    return affix_id(ID.PROSOMAPEDICELLEFT, *i)
