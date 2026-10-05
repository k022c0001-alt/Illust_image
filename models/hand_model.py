# h-*- coding: utf-8 -*-
"""
hand_model.py

手・指の状態を管理するModel。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class HandSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class FingerType(str, Enum):
    THUMB = "thumb"
    INDEX = "index"
    MIDDLE = "middle"
    RING = "ring"
    LITTLE = "little"


@dataclass
class FingerModel:
    """
    1本の指。
    """

    finger_type: FingerType

    base_angle: float = 0.0
    middle_angle: float = 0.0
    tip_angle: float = 0.0

    length: float = 1.0

    locked: bool = False

    def bend(
        self,
        base: float = 0.0,
        middle: float = 0.0,
        tip: float = 0.0,
    ) -> bool:

        if self.locked:
            return False

        self.base_angle += base
        self.middle_angle += middle
        self.tip_angle += tip

        return True


@dataclass
class HandModel:
    """
    片手全体。
    """

    side: HandSide

    fingers: Dict[str, FingerModel] = field(
        default_factory=dict
    )

    wrist_rotation_x: float = 0.0
    wrist_rotation_y: float = 0.0
    wrist_rotation_z: float = 0.0

    palm_scale: float = 1.0

    locked: bool = False

    def create_default_fingers(self) -> None:

        for finger_type in FingerType:

            self.fingers[finger_type.value] = FingerModel(
                finger_type=finger_type
            )

    def get_finger(
        self,
        finger: FingerType
    ) -> FingerModel | None:

        return self.fingers.get(finger.value)

    def bend_finger(
        self,
        finger: FingerType,
        base: float = 0.0,
        middle: float = 0.0,
        tip: float = 0.0,
    ) -> bool:

        target = self.get_finger(finger)

        if target is None:
            return False

        return target.bend(
            base=base,
            middle=middle,
            tip=tip,
        )

    def rotate_wrist(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ) -> bool:

        if self.locked:
            return False

        self.wrist_rotation_x += x
        self.wrist_rotation_y += y
        self.wrist_rotation_z += z

        return True

    def to_dict(self) -> Dict[str, object]:

        return {
            "side": self.side.value,
            "fingers": {
                name: vars(finger)
                for name, finger in self.fingers.items()
            },
            "wrist_rotation_x": self.wrist_rotation_x,
            "wrist_rotation_y": self.wrist_rotation_y,
            "wrist_rotation_z": self.wrist_rotation_z,
            "palm_scale": self.palm_scale,
            "locked": self.locked,
        }
