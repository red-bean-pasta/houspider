from typing import Collection

import hou
from hou import OpNode, SopNode
from houkit.noder import sopify

from .attributes import (
    BodyJoint,
    LegJoint,
    PedipalpJoint,
    body_joint_name,
    leg_joint_name,
    pedipalp_joint_name,
)
from .selector import (
    get_coxa_socket_points,
    get_local_z_direction,
    get_local_z_value,
    get_membrane_boundaries,
    get_pedipalp_socket_points,
    group_membrane_rings,
    traverse_limb_prims,
)


def capture_skin(
    parent: OpNode,
    skin_source: SopNode,
) -> SopNode:
    weighted = sopify(parent, skin_source, assign_skin_weights)
    pack = parent.createNode("captureattribpack", "pack_capture")
    pack.setInput(0, weighted)
    return pack


def deform_skin(
    parent: OpNode,
    captured_skin: SopNode,
    capture_pose: SopNode,
    animated_pose: SopNode,
) -> SopNode:
    deform = parent.createNode("kinefx::jointdeform", "joint_deform")
    deform.setInput(0, captured_skin)
    deform.setInput(1, capture_pose)
    deform.setInput(2, animated_pose)
    return deform


def assign_skin_weights(node: SopNode) -> None:
    geo = node.geometry()
    bone_names = _collect_bone_names()
    bone_indexes = {name: i for i, name in enumerate(bone_names)}
    weights: dict[int, list[tuple[int, float]]] = {}

    _skin_body(geo, bone_indexes, weights)
    _skin_legs(geo, bone_indexes, weights)
    _skin_pedipalps(geo, bone_indexes, weights)
    _write_capture_attributes(geo, bone_names, weights)


def _skin_body(
    geo: hou.Geometry,
    bone_index_map: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    root_idx = bone_index_map[body_joint_name(BodyJoint.ROOT)]
    pedicel_idx = bone_index_map[body_joint_name(BodyJoint.PEDICEL)]

    pedicel_pts: list[hou.Point] = []
    for p in geo.points():
        regions = {pr.stringAttribValue("region") for pr in p.prims()}
        if any(r == "abdomen" for r in regions):
            weights[p.number()] = [(pedicel_idx, 1.0)]
        elif all(r == "pedicel" for r in regions):
            pedicel_pts.append(p)
        else:
            weights[p.number()] = [(root_idx, 1.0)]

    assert pedicel_pts, "Expected pedicel points to exist on geometry"
    z_coords = [p.position().z() for p in pedicel_pts]
    z_min, z_max = min(z_coords), max(z_coords)
    z_span = z_max - z_min
    assert z_span > 1e-6, f"Expected non-zero z span on pedicel, got {z_span}"

    for p in pedicel_pts:
        z = p.position().z()
        t = max(0.0, min(1.0, (z - z_min) / z_span))
        weights[p.number()] = [
            (root_idx, round(1.0 - t, 4)),
            (pedicel_idx, round(t, 4)),
        ]


def _skin_legs(
    geo: hou.Geometry,
    bone_indexes: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    joints = list(LegJoint)
    for is_right in (True, False):
        for i in range(1, 5):
            socket_pts = get_coxa_socket_points(geo, is_right, i)
            bone_names = [leg_joint_name(is_right, i, j) for j in joints]
            _skin_limb(socket_pts, bone_names, bone_indexes, weights)


def _skin_pedipalps(
    geo: hou.Geometry,
    bone_index_map: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    joints = list(PedipalpJoint)
    for is_right in (True, False):
        socket_pts = get_pedipalp_socket_points(geo, is_right)
        bone_names = [pedipalp_joint_name(is_right, j) for j in joints]
        _skin_limb(socket_pts, bone_names, bone_index_map, weights)


def _skin_limb(
    socket_points: list[hou.Point],
    bones: list[str],
    bone_index_map: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    joint_indices = [bone_index_map[name] for name in bones]

    prims, points = traverse_limb_prims(socket_points)
    membranes = group_membrane_rings(prims)

    direction = get_local_z_direction(membranes[0][1])

    soft_pts: set[hou.Point] = set()
    membrane_centers: list[float] = []
    for m_idx, (m_pms, m_pts) in enumerate(membranes):
        boundary1, boundary2 = get_membrane_boundaries(m_pts)
        soft_pts.update(m_pts)
        soft_pts.difference_update(boundary1, boundary2)

        z_center = sum(get_local_z_value(p, direction) for p in m_pts) / len(m_pts)
        membrane_centers.append(z_center)

        _skin_membrane(
            m_pts,
            (joint_indices[m_idx], joint_indices[m_idx + 1]),
            weights,
        )

    seg_pts = [p for p in points if p not in soft_pts]
    for p in seg_pts:
        z = get_local_z_value(p, direction)
        assigned_joint = joint_indices[-2]
        for m_idx, z_mid in enumerate(membrane_centers):
            if z < z_mid:
                assigned_joint = joint_indices[m_idx]
                break
        weights[p.number()] = [(assigned_joint, 1.0)]


def _skin_membrane(
    points: Collection[hou.Point],
    joints: tuple[int, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    direction = get_local_z_direction(points)
    boundary1, boundary2 = get_membrane_boundaries(points)
    z1 = sum(get_local_z_value(p, direction) for p in boundary1) / len(boundary1)
    z2 = sum(get_local_z_value(p, direction) for p in boundary2) / len(boundary2)
    z_span = z2 - z1
    assert z_span > 1e-6

    j_former, j_latter = joints
    soft_pts = set(points) - set(boundary1) - set(boundary2)
    for p in soft_pts:
        z = get_local_z_value(p, direction)
        t = (z - z1) / z_span
        t = max(0.0, min(1.0, t))
        weights[p.number()] = [
            (j_former, round(1.0 - t, 4)),
            (j_latter, round(t, 4)),
        ]


def _collect_bone_names() -> list[str]:
    names = [body_joint_name(j) for j in BodyJoint]
    for is_right in (True, False):
        names.extend(pedipalp_joint_name(is_right, j) for j in PedipalpJoint)
        for leg_idx in range(1, 5):
            names.extend(leg_joint_name(is_right, leg_idx, j) for j in LegJoint)
    return names


def _write_capture_attributes(
    geo: hou.Geometry,
    bone_names: list[str],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    path_attr = geo.addArrayAttrib(hou.attribType.Global, "boneCapture_pCaptPath", hou.attribData.String)
    geo.setGlobalAttribValue(path_attr, bone_names)
    idx_attr = geo.addArrayAttrib(hou.attribType.Point, "boneCapture_index", hou.attribData.Int)
    data_attr = geo.addArrayAttrib(hou.attribType.Point, "boneCapture_data", hou.attribData.Float)

    for p in geo.points():
        w = weights[p.number()]
        p.setAttribValue(idx_attr, tuple(item[0] for item in w))
        p.setAttribValue(data_attr, tuple(item[1] for item in w))
