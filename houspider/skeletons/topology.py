from typing import Callable, Sequence, Iterable

import hou
from houkit.attributer import add_point_attrib
from houkit.topology import add_point

from ..attributes import GlobalAttrib
from .attributes import (
    BodyJoint,
    LegJoint,
    PedipalpJoint,
    body_joint_name, pedipalp_joint_name, leg_joint_name,
)
from .chain import (
    get_body_bone_positions,
    get_leg_bone_positions,
    get_pedipalp_bone_positions,
    get_root_position,
)


def build_body_skeleton(node: hou.SopNode) -> None:
    geo = node.geometry()
    positions = get_body_bone_positions(geo)

    geo.clear()
    _add_name_attrib(geo)
    points = [
        _create_joint_point(geo, pos, name)
        for name, pos in zip(BodyJoint, positions)
    ]
    _wire_branch_polyline(geo, points)


def build_leg_skeletons(node: hou.SopNode) -> None:
    def _get_bone_positions(geo: hou.Geometry) -> Iterable[Iterable[tuple[str, hou.Vector3]]]:
        joint_poses_by_branch: list[Iterable[tuple[str, hou.Vector3]]] = []
        for is_right in (True, False):
            for i in range(1, 5):
                positions = zip(
                    [leg_joint_name(is_right, i, j) for j in LegJoint],
                    get_leg_bone_positions(geo, is_right, i)
                )
                joint_poses_by_branch.append(positions)
        return joint_poses_by_branch

    _build_branch_skeletons(node.geometry(), _get_bone_positions)


def build_pedipalps_skeleton(node: hou.SopNode) -> None:
    def _get_bone_positions(geo: hou.Geometry) -> Iterable[Iterable[tuple[str, hou.Vector3]]]:
        joint_poses_by_branch: list[Iterable[tuple[str, hou.Vector3]]] = []
        for is_right in (True, False):
            positions = zip(
                [pedipalp_joint_name(is_right, j) for j in PedipalpJoint],
                get_pedipalp_bone_positions(geo, is_right)
            )
            joint_poses_by_branch.append(positions)
        return joint_poses_by_branch

    _build_branch_skeletons(node.geometry(), _get_bone_positions)


def add_ik_tags(node: hou.SopNode) -> None:
    geo = node.geometry()
    tags = geo.addArrayAttrib(hou.attribType.Point, "tags", hou.attribData.String)

    for point in geo.points():
        name = point.stringAttribValue("name")
        if name.startswith("leg_") or name.startswith("pedipalp_"):
            tag = "_".join(name.split("_")[:2])
        elif name in (BodyJoint.PEDICEL, BodyJoint.ABDOMEN):
            tag = BodyJoint.ABDOMEN.value
        else:
            tag = ""
        point.setAttribValue(tags, (tag,) if tag else ())


def pose_rest_skeleton(node: hou.SopNode) -> None:
    geo = node.geometry()
    source_geo = node.inputGeometry(1) or geo
    if not source_geo.findGlobalAttrib(GlobalAttrib.JOINT_LIMITS):
        return

    joint_limits = source_geo.dictAttribValue(GlobalAttrib.JOINT_LIMITS)
    min_flex = joint_limits["min_flex_angles"]
    max_flex = joint_limits["max_flex_angles"]
    min_yaw = joint_limits["min_yaw_angles"]
    max_yaw = joint_limits["max_yaw_angles"]
    rest_flex = joint_limits.get(
        "rest_flex_angles",
        tuple(0.5 * (lo + hi) for lo, hi in zip(min_flex, max_flex)),
    )

    leg_joints = list(LegJoint)
    rot_by_joint: dict[str, tuple[float, float, float]] = {}
    for i in range(len(min_flex)):
        jname = leg_joints[i].value
        rx = 180.0 - rest_flex[i]
        ry = 0.5 * (min_yaw[i] + max_yaw[i])
        rot_by_joint[jname] = (rx, ry, 0.0)

    pts = geo.points()
    rest_m4 = [_point_to_matrix4(p) for p in pts]
    posed_m4 = [hou.Matrix4(1.0)] * len(pts)

    for i, pt in enumerate(pts):
        pidx = pt.attribValue("parent_idx")
        m_rest = rest_m4[i]
        if pidx < 0:
            mp_rest = hou.Matrix4(1.0)
            mp_posed = hou.Matrix4(1.0)
        else:
            mp_rest = rest_m4[pidx]
            mp_posed = posed_m4[pidx]

        local_rest = m_rest * mp_rest.inverted()
        name = pt.stringAttribValue("name")
        rx, ry, rz = 0.0, 0.0, 0.0
        if name.startswith("leg_"):
            for jname, rot in rot_by_joint.items():
                if name.endswith(f"_{jname}"):
                    rx, ry, rz = rot
                    break

        r_mat = hou.hmath.buildRotate(rx, ry, rz)
        local_posed = r_mat * local_rest
        mc_posed = local_posed * mp_posed
        posed_m4[i] = mc_posed

        pos = hou.Vector3(mc_posed.at(3, 0), mc_posed.at(3, 1), mc_posed.at(3, 2))
        pt.setPosition(pos)
        m3 = hou.Matrix3((
            mc_posed.at(0, 0), mc_posed.at(0, 1), mc_posed.at(0, 2),
            mc_posed.at(1, 0), mc_posed.at(1, 1), mc_posed.at(1, 2),
            mc_posed.at(2, 0), mc_posed.at(2, 1), mc_posed.at(2, 2),
        ))
        pt.setAttribValue("transform", m3.asTuple())

    _update_local_transforms(geo)


def orient_limb_skeletons(node: hou.SopNode) -> None:
    geo = node.geometry()
    _orient_leg_skeletons(geo)
    _orient_pedipalp_skeletons(geo)
    _update_local_transforms(geo)


def _orient_leg_skeletons(geo: hou.Geometry) -> None:
    pts_by_name = {p.stringAttribValue("name"): p for p in geo.points()}
    for is_right in (True, False):
        for leg_idx in range(1, 5):
            names = [leg_joint_name(is_right, leg_idx, j) for j in LegJoint]
            chain = [pts_by_name[n] for n in names if n in pts_by_name]
            if len(chain) < 2:
                continue

            p0 = chain[0].position()
            p1 = chain[1].position()
            delta = p1 - p0
            dxz = hou.Vector3(delta.x(), 0.0, delta.z()).normalized()
            plane_n = hou.Vector3(-dxz.z(), 0.0, dxz.x()).normalized()

            old_m = hou.Matrix3(chain[0].attribValue("transform"))
            old_x = hou.Vector3(old_m.at(0, 0), old_m.at(0, 1), old_m.at(0, 2))
            if plane_n.dot(old_x) < 0:
                plane_n = -plane_n

            _align_chain_transforms(chain, plane_n)


def _orient_pedipalp_skeletons(geo: hou.Geometry) -> None:
    pts_by_name = {p.stringAttribValue("name"): p for p in geo.points()}
    for is_right in (True, False):
        names = [pedipalp_joint_name(is_right, j) for j in PedipalpJoint]
        chain = [pts_by_name[n] for n in names if n in pts_by_name]
        if len(chain) < 3:
            continue

        p_troch = chain[1].position()
        p_femur = chain[2].position()
        delta = p_femur - p_troch
        dxz = hou.Vector3(delta.x(), 0.0, delta.z()).normalized()
        plane_n = hou.Vector3(-dxz.z(), 0.0, dxz.x()).normalized()

        old_m = hou.Matrix3(chain[1].attribValue("transform"))
        old_x = hou.Vector3(old_m.at(0, 0), old_m.at(0, 1), old_m.at(0, 2))
        if plane_n.dot(old_x) < 0:
            plane_n = -plane_n

        _align_chain_transforms(chain, plane_n)


def _align_chain_transforms(chain: Sequence[hou.Point], plane_n: hou.Vector3) -> None:
    count = len(chain)
    for i, pt in enumerate(chain):
        if i < count - 1:
            aim_z = (chain[i + 1].position() - pt.position()).normalized()
        else:
            aim_z = (pt.position() - chain[i - 1].position()).normalized()

        axis_x = plane_n
        axis_y = aim_z.cross(axis_x).normalized()
        if axis_x.cross(axis_y).dot(aim_z) < 0:
            axis_y = -axis_y

        m = hou.Matrix3((
            axis_x.x(), axis_x.y(), axis_x.z(),
            axis_y.x(), axis_y.y(), axis_y.z(),
            aim_z.x(), aim_z.y(), aim_z.z(),
        ))
        pt.setAttribValue("transform", m.asTuple())


def _update_local_transforms(geo: hou.Geometry) -> None:
    if geo.findPointAttrib("localtransform") is None or geo.findPointAttrib("parent_idx") is None:
        return
    for p in geo.points():
        parent_idx = p.attribValue("parent_idx")
        if parent_idx >= 0:
            parent_pt = geo.point(parent_idx)
            mc = _point_to_matrix4(p)
            mp = _point_to_matrix4(parent_pt)
            local_m4 = mc * mp.inverted()
            p.setAttribValue("localtransform", local_m4.asTuple())


def _point_to_matrix4(pt: hou.Point) -> hou.Matrix4:
    m3 = hou.Matrix3(pt.attribValue("transform"))
    pos = pt.position()
    return hou.Matrix4((
        m3.at(0, 0), m3.at(0, 1), m3.at(0, 2), 0.0,
        m3.at(1, 0), m3.at(1, 1), m3.at(1, 2), 0.0,
        m3.at(2, 0), m3.at(2, 1), m3.at(2, 2), 0.0,
        pos.x(), pos.y(), pos.z(), 1.0,
    ))


def _build_branch_skeletons(
        geo: hou.Geometry,
        get_branch_positions: Callable[
            [hou.Geometry],
            Iterable[Iterable[tuple[str, hou.Vector3]]]
        ],
) -> None:
    root_joint_pos = get_root_position(geo)
    joint_poses_by_branch = get_branch_positions(geo)

    geo.clear()
    _add_name_attrib(geo)

    root_pt = _create_joint_point(geo, root_joint_pos, body_joint_name(BodyJoint.ROOT))
    for named_poses_branch in joint_poses_by_branch:
        leg_pts = [
            _create_joint_point(geo, pos, name)
            for name, pos in
            named_poses_branch
        ]
        _wire_branch_polyline(geo, [root_pt, *leg_pts])


def _wire_branch_polyline(
    geo: hou.Geometry,
    chain_points: Sequence[hou.Point],
) -> hou.Polygon:
    assert len(chain_points) >= 2, "Expected at least 2 points to wire polyline"
    poly = geo.createPolygon()
    poly.setIsClosed(False)
    for pt in chain_points:
        poly.addVertex(pt)
    return poly


def _add_name_attrib(
    geo: hou.Geometry,
) -> hou.Attrib:
    return add_point_attrib(geo, "name", "")


def _create_joint_point(
    geo: hou.Geometry,
    pos: hou.Vector3,
    name: str,
    attribute: hou.Attrib | str = "name",
) -> hou.Point:
    return add_point(geo, pos, (attribute, name))
