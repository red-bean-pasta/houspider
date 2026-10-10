import math
import re
from collections.abc import Callable

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
from ..legs.attributes import legmembrane, legsegment, legsegmentbuffer, legsegmentinset
from ..pedipalps.attributes import pedipalpcoxabuffer, pedipalpmembrane, pedipalpsegment, pedipalpsegmentinset


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


def extrude_deformed_membranes(node: SopNode) -> None:
    geo = node.geometry()
    inputs = node.inputs()
    rest_geo = inputs[1].geometry() if len(inputs) > 1 and inputs[1] is not None else None
    _extrude_membrane_midpoints(geo, rest_geo)


def _extrude_membrane_midpoints(geo: hou.Geometry, rest_geo: hou.Geometry | None) -> None:
    id_attr = geo.findPointAttrib("id")
    if id_attr is None:
        return

    pts_by_id = {p.stringAttribValue(id_attr): p for p in geo.points()}
    rest_pts_by_id = (
        {p.stringAttribValue("id"): p for p in rest_geo.points() if rest_geo.findPointAttrib("id")}
        if rest_geo is not None
        else pts_by_id
    )

    prefixes = set()
    for pid in pts_by_id.keys():
        match = re.match(r"^((?:leg|pedipalp)membrane[^_]+_\d+)_mid_[12]$", pid)
        if match:
            prefixes.add(match.group(1))

    for prefix in prefixes:
        _extrude_single_membrane_joint(prefix, pts_by_id, rest_pts_by_id)


def _extrude_single_membrane_joint(
    prefix: str,
    pts_by_id: dict[str, hou.Point],
    rest_pts_by_id: dict[str, hou.Point],
) -> None:
    for corner in (1, 2):
        top_corner = 4 if corner == 1 else 3
        pid_mid = f"{prefix}_mid_{corner}"
        pid_f = f"{prefix}_1_{corner}"
        pid_l = f"{prefix}_-1_{corner}"
        pid_top = f"{prefix}_mid_{top_corner}"

        p_mid = pts_by_id.get(pid_mid)
        p_f = pts_by_id.get(pid_f)
        p_l = pts_by_id.get(pid_l)
        p_top = pts_by_id.get(pid_top)

        rest_p_f = rest_pts_by_id.get(pid_f)
        rest_p_l = rest_pts_by_id.get(pid_l)

        if not (p_mid and p_f and p_l and p_top and rest_p_f and rest_p_l):
            continue

        l_rest_gap = rest_p_f.position().distanceTo(rest_p_l.position())
        pos_f = p_f.position()
        pos_l = p_l.position()
        pos_top = p_top.position()

        gap_vec = pos_l - pos_f
        d_gap = gap_vec.length()
        if d_gap >= l_rest_gap or d_gap < 1e-6:
            continue

        chord_center = (pos_f + pos_l) * 0.5
        gap_dir = gap_vec.normalized()

        outward_dir = chord_center - pos_top
        outward_dir = outward_dir - gap_dir * outward_dir.dot(gap_dir)
        if outward_dir.length() < 1e-6:
            continue
        outward_dir = outward_dir.normalized()

        h = 0.5 * math.sqrt(l_rest_gap ** 2 - d_gap ** 2)
        p_mid.setPosition(chord_center + outward_dir * h)


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
    _skin_single_limb(
        id_to_point, joint_indices, weights,
        legsegmentbuffer(leg_idx, 1, ""),
        lambda seg: legsegment(leg_idx, seg),
        lambda joint, loop, corner: legmembrane(leg_idx, joint, loop, corner),
        lambda seg, direction, corner: legsegmentinset(leg_idx, seg, direction, corner),
    )


def _skin_single_pedipalp(
    id_to_point: dict[str, hou.Point],
    side: int,
    joint_indices: list[int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    _skin_single_limb(
        id_to_point, joint_indices, weights,
        pedipalpcoxabuffer(side),
        lambda seg: pedipalpsegment(side, seg),
        lambda joint, loop, corner: pedipalpmembrane(side, joint, loop, corner),
        lambda seg, direction, corner: pedipalpsegmentinset(side, seg, direction, corner),
    )


def _skin_single_limb(
    id_to_point: dict[str, hou.Point],
    joint_indices: list[int],
    weights: dict[int, list[tuple[int, float]]],
    buffer_prefix: str,
    segment_id: Callable[[int], str],
    membrane_id: Callable[[int, int | str, int], str],
    inset_id: Callable[[int, int, int], str],
) -> None:
    coxa_bone = joint_indices[0]
    for pid, pt in id_to_point.items():
        if pid.startswith(buffer_prefix):
            weights[pt.number()] = [(coxa_bone, 1.0)]

    for seg_idx, seg_bone in enumerate(joint_indices, start=1):
        seg_prefix = segment_id(seg_idx)
        for pid, pt in id_to_point.items():
            if pid.startswith(seg_prefix) and not pid.startswith(buffer_prefix):
                weights[pt.number()] = [(seg_bone, 1.0)]

    for joint_idx in range(1, len(joint_indices)):
        j_former = joint_indices[joint_idx - 1]
        j_latter = joint_indices[joint_idx]

        for corner_idx in (3, 4):
            for loop_idx in (1, "mid", -1):
                pid = membrane_id(joint_idx, loop_idx, corner_idx)
                if pid in id_to_point:
                    weights[id_to_point[pid].number()] = [(j_latter, 1.0)]

        for corner_idx in (1, 2):
            pts = [
                id_to_point.get(inset_id(joint_idx, -1, corner_idx)),
                id_to_point.get(membrane_id(joint_idx, 1, corner_idx)),
                id_to_point.get(membrane_id(joint_idx, "mid", corner_idx)),
                id_to_point.get(membrane_id(joint_idx, -1, corner_idx)),
                id_to_point.get(inset_id(joint_idx + 1, 1, corner_idx)),
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
