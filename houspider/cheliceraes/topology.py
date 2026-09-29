import hou

from ..dorsals.attributes import dorsalbasesupport, dorsalchelicerae
from ..helper import rename_left_ids as rename_left_ids_geometry

# noinspection PyUnusedImports
from .geometry import (
    build_geometry,
)
# noinspection PyUnusedImports
from .membrane import (
    inset_flaps,
    classify_after_inset,
    prepare_extrusion,
    remove_left_membrane,
    add_start_membrane,
    inset_start_membrane,
    adjust_start_section_left,
)
# noinspection PyUnusedImports
from .sections import (
    add_end_section,
    add_middle_section,
    add_upper_middle_section,
    add_lower_middle_section,
    connect_sections,
)
# noinspection PyUnusedImports
from .support import (
    remove_middle_face,
    middle_loop_cut,
    merge_membrane_curves,
    adjust_start_membrane_curve,
    adjust_right_membrane_width,
    adjust_dorsal_chelicerae_depth,
    inset_chelicerae_support_loop,
    add_start_membrane_support_loops,
    add_start_section_support_loops,
)


def rename_left_ids(node: hou.SopNode) -> None:
    rename_left_ids_geometry(node.geometry(), affix_index=-1)


def deduplicate_base_faces(node: hou.SopNode) -> None:
    geo: hou.Geometry = node.geometry()
    base_id_sets = []
    for sign in (1, -1):
        base_id_sets.append({
            dorsalchelicerae(0),
            dorsalchelicerae(sign * 1),
            dorsalbasesupport(dorsalchelicerae(sign * 1)),
            dorsalbasesupport(dorsalchelicerae(0)),
        })
        base_id_sets.append({
            dorsalchelicerae(sign * 1),
            dorsalchelicerae(sign * 2),
            dorsalbasesupport(dorsalchelicerae(sign * 2)),
            dorsalbasesupport(dorsalchelicerae(sign * 1)),
        })

    duplicate_prims = [
        prim for prim in geo.prims()
        if {pt.stringAttribValue("id") for pt in prim.points()} in base_id_sets
    ]
    geo.deletePrims(duplicate_prims, keep_points=False)
