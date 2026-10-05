# -*- coding: utf-8 -*-
"""
frame_model.py

アニメーションの1フレームを管理するModel。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class FrameQuality:
    """
    フレーム品質評価。
    """

    overall: float = 0.0

    face: float = 0.0
    body: float = 0.0
    hands: float = 0.0
    limbs: float = 0.0
    style: float = 0.0

    passed: bool = False

    issues: list[str] = field(
        default_factory=list
    )


@dataclass
class FrameModel:
    """
    1枚のアニメーションフレーム。
    """

    frame_id: str

    frame_index: int

    image_path: Optional[str] = None

    pose_id: Optional[str] = None

    is_keyframe: bool = False

    generated_by_ai: bool = False

    quality: FrameQuality = field(
        default_factory=FrameQuality
    )

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    def mark_generated(self) -> None:
        self.generated_by_ai = True

    def add_issue(
        self,
        issue: str
    ) -> None:

        if issue and issue not in self.quality.issues:
            self.quality.issues.append(issue)

    def to_dict(self) -> Dict[str, object]:

        return {
            "frame_id": self.frame_id,
            "frame_index": self.frame_index,
            "image_path": self.image_path,
            "pose_id": self.pose_id,
            "is_keyframe": self.is_keyframe,
            "generated_by_ai": self.generated_by_ai,
            "quality": vars(self.quality),
            "metadata": self.metadata,
        }
