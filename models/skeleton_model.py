# -*- coding: utf-8 -*-
"""
skeleton_model.py

キャラクターの身体構造・関節・骨格を定義します。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class JointType(str, Enum):
    HEAD = "head"
    NECK = "neck"

    LEFT_SHOULDER = "left_shoulder"
    LEFT_ELBOW = "left_elbow"
    LEFT_WRIST = "left_wrist"

    RIGHT_SHOULDER = "right_shoulder"
    RIGHT_ELBOW = "right_elbow"
    RIGHT_WRIST = "right_wrist"

    CHEST = "chest"
    WAIST = "waist"
    PELVIS = "pelvis"

    LEFT_HIP = "left_hip"
    LEFT_KNEE = "left_knee"
    LEFT_ANKLE = "left_ankle"

    RIGHT_HIP = "right_hip"
    RIGHT_KNEE = "right_knee"
    RIGHT_ANKLE = "right_ankle"


@dataclass
class Joint:
    """
    1つの関節。
    """

    name: str

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

    parent: Optional[str] = None

    confidence: float = 1.0

    locked: bool = False


@dataclass
class SkeletonModel:
    """
    キャラクターの骨格。

    座標は基本的に正規化座標を想定します。
    """

    joints: Dict[str, Joint] = field(
        default_factory=dict
    )

    root_joint: str = "pelvis"

    def add_joint(self, joint: Joint) -> None:
        self.joints[joint.name] = joint

    def get_joint(self, name: str) -> Optional[Joint]:
        return self.joints.get(name)

    def lock_joint(self, name: str) -> None:
        joint = self.get_joint(name)

        if joint:
            joint.locked = True

    def unlock_joint(self, name: str) -> None:
        joint = self.get_joint(name)

        if joint:
            joint.locked = False

    def rotate_joint(
        self,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ) -> bool:
        """
        関節を回転させる。

        locked=Trueの場合は変更しません。
        """

        joint = self.get_joint(name)

        if joint is None:
            return False

        if joint.locked:
            return False

        joint.rotation_x += x
        joint.rotation_y += y
        joint.rotation_z += z

        return True

    def to_dict(self) -> Dict[str, object]:
        return {
            "root_joint": self.root_joint,
            "joints": {
                name: vars(joint)
                for name, joint in self.joints.items()
            },

        }
