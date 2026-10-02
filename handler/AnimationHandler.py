# -*- coding: utf-8 -*-
"""
animation_handler.py

アニメーション制作全体を管理するHandler。
"""

from typing import Any, Dict, List

from .base_handler import BaseHandler, HandlerResult
from .pose_handler import PoseHandler
from .rotation_handler import RotationHandler
from .face_handler import FaceHandler
from .hand_handler import HandHandler

from ..models.animation_model import (
    AnimationModel,
    AnimationFrame,
)

from ..models.pose_model import PoseModel
from ..models.face_model import FaceModel


class AnimationHandler(BaseHandler):

    name = "animation"

    def __init__(self):

        super().__init__()

        self.pose_handler = PoseHandler()
        self.rotation_handler = RotationHandler()
        self.face_handler = FaceHandler()
        self.hand_handler = HandHandler()

    def handle(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        action = request.get("action")

        try:

            if action == "apply_pose":
                return self.apply_pose(request)

            if action == "rotate":
                return self.rotation_handler.handle(
                    request
                )

            if action == "face":
                return self.face_handler.handle(
                    request
                )

            if action == "hand":
                return self.hand_handler.handle(
                    request
                )

            if action == "create_frames":
                return self.create_frames(request)

            return self.failure(
                f"unknown animation action: {action}"
            )

        except Exception as exc:

            return self.failure(
                "animation processing failed",
                [str(exc)],
            )

    def apply_pose(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        return self.pose_handler.handle(
            request
        )

    def create_frames(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        animation = request.get(
            "animation"
        )

        if not isinstance(
            animation,
            AnimationModel,
        ):

            return self.failure(
                "animation must be AnimationModel"
            )

        poses = request.get(
            "poses",
            [],
        )

        if not isinstance(poses, list):

            return self.failure(
                "poses must be list"
            )

        for index, pose in enumerate(poses):

            if not isinstance(
                pose,
                PoseModel,
            ):
                continue

            animation.add_pose(pose)

            frame = AnimationFrame(
                frame_id=f"{animation.animation_id}_frame_{index:04d}",
                frame_index=index,
                pose_id=pose.pose_id,
                is_keyframe=True,
            )

            animation.add_frame(frame)

        animation.duration_seconds = (
            animation.calculate_duration()
        )

        return self.success(
            animation,
            f"{len(poses)} frames created",
        )
