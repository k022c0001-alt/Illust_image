# -*- coding: utf-8 -*-
"""
face_model.py

キャラクターの顔・表情・視線・頭部回転を定義します。
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class FaceModel:
    """
    顔の状態。

    値は基本的に正規化・角度ベースで管理します。
    """

    head_rotation_x: float = 0.0
    head_rotation_y: float = 0.0
    head_rotation_z: float = 0.0

    eye_direction_x: float = 0.0
    eye_direction_y: float = 0.0

    left_eye_open: float = 1.0
    right_eye_open: float = 1.0

    eyebrow_left: float = 0.0
    eyebrow_right: float = 0.0

    mouth_open: float = 0.0
    mouth_curve: float = 0.0

    expression: str = "neutral"

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    def rotate_head(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ) -> None:

        self.head_rotation_x += x
        self.head_rotation_y += y
        self.head_rotation_z += z

    def set_expression(
        self,
        expression: str
    ) -> None:

        self.expression = expression

    def to_dict(self) -> Dict[str, object]:

        return vars(self).copy()
