# -*- coding: utf-8 -*-
"""
pose_model.py

キャラクターのポーズ情報を定義します。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class JointPose:
    """
    1つの関節に対するポーズ情報。
    """

    joint_name: str

    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0


@dataclass
class PoseModel:
    """
    キャラクター全体のポーズ。
    """

    pose_id: str

    name: str = ""

    joints: Dict[str, JointPose] = field(
        default_factory=dict
    )

    description: str = ""

    tags: List[str] = field(
        default_factory=list
    )

    parent_pose_id: Optional[str] = None

    def set_joint_pose(
        self,
        joint_name: str,
        rotation_x: float = 0.0,
        rotation_y: float = 0.0,
        rotation_z: float = 0.0,
    ) -> None:

        self.joints[joint_name] = JointPose(
            joint_name=joint_name,
            rotation_x=rotation_x,
            rotation_y=rotation_y,
            rotation_z=rotation_z,
        )

    def get_joint_pose(
        self,
        joint_name: str
    ) -> Optional[JointPose]:

        return self.joints.get(joint_name)

    def add_tag(self, tag: str) -> None:

        if tag and tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, object]:

        return {
            "pose_id": self.pose_id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "parent_pose_id": self.parent_pose_id,
            "joints": {
                name: vars(pose)
                for name, pose in self.joints.items()
            },
        }
