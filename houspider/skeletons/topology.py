from typing import Callable, Sequence, Iterable

import hou
from houkit.attributer import add_point_attrib
from houkit.topology import add_point

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
