from collections.abc import Callable

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
from ..legs.attributes import ID as LegID, legmembrane, legsegment
from ..pedipalps.attributes import ID as PedipalpID, pedipalpmembrane, pedipalpsegment


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
    joints = list(LegJoint)
    for is_right in (True, False):
        for leg_idx in range(1, 5):
            affix_idx = leg_idx if is_right else -leg_idx
            bone_names = [leg_joint_name(is_right, leg_idx, j) for j in joints]
            joint_indices = [bone_indexes[name] for name in bone_names]

            _skin_limb_attributes(
                geo=geo,
                side_idx=affix_idx,
                num_segments=7,
                joint_indices=joint_indices,
                weights=weights,
                segment_id_fn=lambda seg, loop, corner, s=affix_idx: legsegment(s, seg, loop, corner),
                membrane_id_fn=lambda jnt, loop, corner, s=affix_idx: legmembrane(s, jnt, loop, corner),
                buffer_prefix=f"{LegID.LEGSEGMENT}{affix_idx}_1_buffer",
            )


def _skin_pedipalps(
    geo: hou.Geometry,
    bone_index_map: dict[str, int],
    weights: dict[int, list[tuple[int, float]]],
) -> None:
    joints = list(PedipalpJoint)
    for is_right in (True, False):
        side = 1 if is_right else -1
        bone_names = [pedipalp_joint_name(is_right, j) for j in joints]
        joint_indices = [bone_index_map[name] for name in bone_names]

        _skin_limb_attributes(
            geo=geo,
            side_idx=side,
            num_segments=6,
            joint_indices=joint_indices,
            weights=weights,
            segment_id_fn=lambda seg, loop, corner, s=side: pedipalpsegment(s, seg, loop, corner),
            membrane_id_fn=lambda jnt, loop, corner, s=side: pedipalpmembrane(s, jnt, loop, corner),
            buffer_prefix=f"{PedipalpID.PEDIPALPSEGMENT}{side}_1_buffer",
        )


def _skin_limb_attributes(
    geo: hou.Geometry,
    side_idx: int,
    num_segments: int,
    joint_indices: list[int],
    weights: dict[int, list[tuple[int, float]]],
    segment_id_fn: Callable[[int | str, int | str, int | str], str],
    membrane_id_fn: Callable[[int | str, int | str, int | str], str],
    buffer_prefix: str,
) -> None:
    """Skin all segments and membranes of a limb using direct attribute references."""
    id_to_point: dict[str, hou.Point] = {}
    for p in geo.points():
        pid = p.attribValue("id")
        if pid:
            id_to_point[pid] = p

    # 1. Skin coxa socket buffer points 100% to coxa bone (joint_indices[0])
    coxa_bone = joint_indices[0]
    for pid, pt in id_to_point.items():
        if pid.startswith(buffer_prefix):
            weights[pt.number()] = [(coxa_bone, 1.0)]

    # 2. Skin segments (1..num_segments): 100% to each segment's bone
    for seg_idx in range(1, num_segments + 1):
        seg_bone = joint_indices[seg_idx - 1]
        loops = [2, 3, 4, 5]
        if seg_idx > 1:
            loops.append(1)  # start inset
        if seg_idx < num_segments:
            loops.append(6)  # end inset

        for loop_idx in loops:
            for corner_idx in range(1, 5):
                pid = segment_id_fn(seg_idx, loop_idx, corner_idx)
                if pid in id_to_point:
                    weights[id_to_point[pid].number()] = [(seg_bone, 1.0)]

    # 3. Skin membranes (1..num_joints):
    # Upper corners (3: ru, 4: lu) are 100% skinned to latter segment bone.
    # Bottom corners (1: lb, 2: rb) are skinned based on cumulative distance along corner line:
    #   p0: former segment end inset (loop 6)
    #   p1: membrane support 1 (loop 1)
    #   p2: membrane middle (loop 2)
    #   p3: membrane support 2 (loop 3)
    #   p4: latter segment start inset (loop 1)
    num_joints = num_segments - 1
    for joint_idx in range(1, num_joints + 1):
        j_former = joint_indices[joint_idx - 1]
        j_latter = joint_indices[joint_idx]

        # Upper corners: 100% latter segment
        for corner_idx in (3, 4):
            for loop_idx in (1, 2, 3):
                pid = membrane_id_fn(joint_idx, loop_idx, corner_idx)
                if pid in id_to_point:
                    weights[id_to_point[pid].number()] = [(j_latter, 1.0)]

        # Bottom corners: cumulative distance along corner path
        for corner_idx in (1, 2):
            id_p0 = segment_id_fn(joint_idx, 6, corner_idx)
            id_p1 = membrane_id_fn(joint_idx, 1, corner_idx)
            id_p2 = membrane_id_fn(joint_idx, 2, corner_idx)
            id_p3 = membrane_id_fn(joint_idx, 3, corner_idx)
            id_p4 = segment_id_fn(joint_idx + 1, 1, corner_idx)

            pts = [id_to_point[x] for x in (id_p0, id_p1, id_p2, id_p3, id_p4)]
            dists = [0.0]
            for a, b in zip(pts[:-1], pts[1:]):
                dists.append(dists[-1] + a.position().distanceTo(b.position()))
            total_d = dists[-1]
            assert total_d > 1e-6, f"Expected non-zero corner line distance at joint {joint_idx}"

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
