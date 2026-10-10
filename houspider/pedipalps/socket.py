import hou

from ..bases.attributes import basemaxillamembrane
from ..helper import positions_from_geo


def get_pedipalp_socket_size(geo: hou.Geometry, hw_ratio: float) -> tuple[float, float]:
    width = get_pedipalp_coxa_socket_width(geo)
    height = width * hw_ratio
    return width, height


def get_pedipalp_coxa_socket_width(geo: hou.Geometry) -> float:
    m3, m4 = positions_from_geo(
        geo,
        basemaxillamembrane(3),
        basemaxillamembrane(4),
    )
    return m3.distanceTo(m4)
