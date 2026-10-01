import hou

from ..bases.attributes import basemaxillamembrane
from ..helper import positions_from_geo


def get_pedipalp_socket_size(geo: hou.Geometry) -> tuple[float, float]:
    m1, m3, m4 = positions_from_geo(
        geo,
        basemaxillamembrane(1),
        basemaxillamembrane(3),
        basemaxillamembrane(4),
    )
    return m3.distanceTo(m4), m3.distanceTo(m1)
