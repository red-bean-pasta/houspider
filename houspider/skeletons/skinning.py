import hou
from hou import OpNode, SopNode
from houkit.noder import sopify

from ..helper import points_by_id
from .attributes import (
    BodyJoint,
    LegJoint,
    PedipalpJoint,
    body_joint_name,
    leg_joint_name,
    pedipalp_joint_name,
)
from ..legs.attributes import legmembrane, legmembranemid, legsegment, legsegmentbuffer, legsegmentinset
from ..pedipalps.attributes import pedipalpcoxabuffer, pedipalpmembrane, pedipalpmembranemid, pedipalpsegment, pedipalpsegmentinset


def capture_skin(
    parent: OpNode,
    skin_source: SopNode,
) -> SopNode:
    weighted = sopify(parent, skin_source, assign_skin_weights)
    pack = parent.createNode("captureattribpack", "pack_capture")
    pack.setInput(0, weighted)
    return pack


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
        pid = p.attribValue("id")
        if pid.startswith("leg") or pid.startswith("pedipalp"):
            continue

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
    id_to_point = points_by_id(geo)
    joints = list(LegJoint)
    for is_right in (True, False):
        for leg_idx in range(1, 5):
            affix_idx = leg_idx if is_right else -leg_idx
            bone_names = [leg_joint_name(is_right, leg_idx, j) for j in joints]
            joint_indices = [bone_indexes[name] for name in bone_names]
            _skin_single_leg(id_to_point, affix_idx, joint_indices, weights)


def _skin_pedipalps(
    geo: hou.Geometry,
    bone_index_map: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    id_to_point = points_by_id(geo)
    joints = list(PedipalpJoint)
    for is_right in (True, False):
        side = 1 if is_right else -1
        bone_names = [pedipalp_joint_name(is_right, j) for j in joints]
        joint_indices = [bone_index_map[name] for name in bone_names]
        _skin_single_pedipalp(id_to_point, side, joint_indices, weights)


def _skin_single_leg(
    id_to_point: dict[str, hou.Point],
    leg_idx: int,
    joint_indices: list[int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    coxa_bone = joint_indices[0]
    buffer_prefix = legsegmentbuffer(leg_idx, 1, "")
    for pid, pt in id_to_point.items():
        if pid.startswith(buffer_prefix):
            weights[pt.number()] = [(coxa_bone, 1.0)]

    for seg_idx, seg_bone in enumerate(joint_indices, start=1):
        seg_prefix = legsegment(leg_idx, seg_idx)
        for pid, pt in id_to_point.items():
            if pid.startswith(seg_prefix) and not pid.startswith(buffer_prefix):
                weights[pt.number()] = [(seg_bone, 1.0)]

    for joint_idx in range(1, len(joint_indices)):
        j_former = joint_indices[joint_idx - 1]
        j_latter = joint_indices[joint_idx]

        for corner_idx in (3, 4):
            for loop_idx in (1, "mid", -1):
                pid = legmembrane(leg_idx, joint_idx, loop_idx, corner_idx)
                if pid in id_to_point:
                    weights[id_to_point[pid].number()] = [(j_latter, 1.0)]

        for corner_idx in (1, 2):
            pts = [
                id_to_point.get(legsegmentinset(leg_idx, joint_idx, -1, corner_idx)),
                id_to_point.get(legmembrane(leg_idx, joint_idx, 1, corner_idx)),
                id_to_point.get(legmembranemid(leg_idx, joint_idx, corner_idx)),
                id_to_point.get(legmembrane(leg_idx, joint_idx, -1, corner_idx)),
                id_to_point.get(legsegmentinset(leg_idx, joint_idx + 1, 1, corner_idx)),
            ]
            _skin_membrane_corner_line(pts, j_former, j_latter, weights)


def _skin_single_pedipalp(
    id_to_point: dict[str, hou.Point],
    side: int,
    joint_indices: list[int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    coxa_bone = joint_indices[0]
    buffer_prefix = pedipalpcoxabuffer(side)
    for pid, pt in id_to_point.items():
        if pid.startswith(buffer_prefix):
            weights[pt.number()] = [(coxa_bone, 1.0)]

    for seg_idx, seg_bone in enumerate(joint_indices, start=1):
        seg_prefix = pedipalpsegment(side, seg_idx)
        for pid, pt in id_to_point.items():
            if pid.startswith(seg_prefix) and not pid.startswith(buffer_prefix):
                weights[pt.number()] = [(seg_bone, 1.0)]

    for joint_idx in range(1, len(joint_indices)):
        j_former = joint_indices[joint_idx - 1]
        j_latter = joint_indices[joint_idx]

        for corner_idx in (3, 4):
            for loop_idx in (1, "mid", -1):
                pid = pedipalpmembrane(side, joint_idx, loop_idx, corner_idx)
                if pid in id_to_point:
                    weights[id_to_point[pid].number()] = [(j_latter, 1.0)]

        for corner_idx in (1, 2):
            pts = [
                id_to_point.get(pedipalpsegmentinset(side, joint_idx, -1, corner_idx)),
                id_to_point.get(pedipalpmembrane(side, joint_idx, 1, corner_idx)),
                id_to_point.get(pedipalpmembranemid(side, joint_idx, corner_idx)),
                id_to_point.get(pedipalpmembrane(side, joint_idx, -1, corner_idx)),
                id_to_point.get(pedipalpsegmentinset(side, joint_idx + 1, 1, corner_idx)),
            ]
            _skin_membrane_corner_line(pts, j_former, j_latter, weights)


def _skin_membrane_corner_line(
    pts: list[hou.Point | None],
    j_former: int,
    j_latter: int,
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    if any(p is None for p in pts):
        return
    dists = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        dists.append(dists[-1] + a.position().distanceTo(b.position()))
    total_d = dists[-1]
    assert total_d > 1e-6, "Expected non-zero corner line distance"

    for idx, pt in enumerate(pts[1:4], start=1):
        t = max(0.0, min(1.0, dists[idx] / total_d))
        weights[pt.number()] = [
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
