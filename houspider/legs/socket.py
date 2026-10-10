import hou

from ..bases.attributes import basecoxamemebrane, basecoxamembranemiddle
from ..helper import points_from_geo


def get_front_coxa_socket_hw_ratio(geo: hou.Geometry) -> float:
    return get_front_coxa_socket_height(geo) / get_front_coxa_socket_width(geo)


def get_front_coxa_socket_width(geo: hou.Geometry) -> float:
    pos_top_sz, pos_top_bz = points_from_geo(
        geo,
        basecoxamemebrane(1, 4),
        basecoxamemebrane(1, 3),
    )
    return (pos_top_bz.position() - pos_top_sz.position()).length()


def get_front_coxa_socket_height(geo: hou.Geometry) -> float:
    pos_top_sz, pos_btm_sz = points_from_geo(
        geo,
        basecoxamembranemiddle(1, 2),
        basecoxamembranemiddle(1, 1),
    )
    return (pos_top_sz.position() - pos_btm_sz.position()).length()
