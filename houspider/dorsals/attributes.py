from enum import StrEnum, auto

from ..helper import affix_id


class ID(StrEnum):
    DORSALCHELICERAE = auto()
    DORSALFRONT = auto()
    DORSALBACK = auto()
    DORSALTOPMIDDLE = auto()
    DORSALSIDEFRONT = auto()
    DORSALSIDEMIDDLE = auto()
    DORSALSIDEBACK = auto()
    DORSALSUPPORT = auto()
    DORSALBASESUPPORT = auto()
    DORSALFRONTFLOAT = auto()
    DORSALFRONTMID = auto()


class Region(StrEnum):
    DORSALFRONTMAIN = auto()
    DORSALFRONTCHEEK = auto()
    DORSALTOP = auto()
    DORSALBACK = auto()
    DORSALSIDE = auto()


def dorsalchelicerae(*i: int | str) -> str:
    return affix_id(ID.DORSALCHELICERAE, *i)


def dorsalfront(*i: int | str) -> str:
    return affix_id(ID.DORSALFRONT, *i)


def dorsalback(*i: int | str) -> str:
    return affix_id(ID.DORSALBACK, *i)


def dorsaltopmiddle(*i: int | str) -> str:
    return affix_id(ID.DORSALTOPMIDDLE, *i)


def dorsalsidefront(*i: int | str) -> str:
    return affix_id(ID.DORSALSIDEFRONT, *i)


def dorsalsidemiddle(*i: int | str) -> str:
    return affix_id(ID.DORSALSIDEMIDDLE, *i)


def dorsalsideback(*i: int | str) -> str:
    return affix_id(ID.DORSALSIDEBACK, *i)


def dorsalsupport(*i: int | str) -> str:
    return affix_id(ID.DORSALSUPPORT, *i)


def dorsalbasesupport(*i: int | str) -> str:
    return affix_id(f"{ID.DORSALBASESUPPORT}_", *i)


def dorsalfrontfloat(*i: int | str) -> str:
    return affix_id(ID.DORSALFRONTFLOAT, *i)


def dorsalfrontmid(*i: int | str) -> str:
    return affix_id(ID.DORSALFRONTMID, *i)
