# -*- coding: utf-8 -*-
"""
hand_handler.py

手・指のポーズを操作するHandler。
"""

from typing import Any, Dict

from .base_handler import BaseHandler, HandlerResult
from ..models.hand_model import (
    HandModel,
    HandSide,
    FingerType,
)


class HandHandler(BaseHandler):

    name = "hand"

    def handle(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        try:
            action = request.get("action")

            if action == "bend":
                return self.bend_finger(request)

            if action == "open":
                return self.open_hand(request)

            if action == "fist":
                return self.make_fist(request)

            if action == "peace":
                return self.make_peace(request)

            return self.failure(
                f"unknown hand action: {action}"
            )

        except Exception as exc:

            return self.failure(
                "hand processing failed",
                [str(exc)],
            )

    def _get_hand(
        self,
        request: Dict[str, Any],
    ) -> HandModel:

        hand = request.get("hand")

        if not isinstance(hand, HandModel):
            raise ValueError(
                "hand must be HandModel"
            )

        return hand

    def bend_finger(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        hand = self._get_hand(request)

        finger_name = request.get(
            "finger",
            "index",
        )

        try:
            finger = FingerType(finger_name)
        except ValueError:

            return self.failure(
                f"unknown finger: {finger_name}"
            )

        result = hand.bend_finger(
            finger,
            base=float(request.get("base", 20)),
            middle=float(request.get("middle", 20)),
            tip=float(request.get("tip", 20)),
        )

        if not result:
            return self.failure(
                "finger operation failed"
            )

        return self.success(
            hand,
            f"{finger_name} bent",
        )

    def open_hand(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        hand = self._get_hand(request)

        for finger in hand.fingers.values():

            finger.base_angle = 0
            finger.middle_angle = 0
            finger.tip_angle = 0

        return self.success(
            hand,
            "hand opened",
        )

    def make_fist(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        hand = self._get_hand(request)

        for finger in hand.fingers.values():

            if finger.finger_type == FingerType.THUMB:
                continue

            finger.base_angle = 80
            finger.middle_angle = 80
            finger.tip_angle = 80

        return self.success(
            hand,
            "fist pose created",
        )

    def make_peace(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:

        hand = self._get_hand(request)

        index = hand.get_finger(
            FingerType.INDEX
        )

        middle = hand.get_finger(
            FingerType.MIDDLE
        )

        if index:
            index.base_angle = 0
            index.middle_angle = 0
            index.tip_angle = 0

        if middle:
            middle.base_angle = 0
            middle.middle_angle = 0
            middle.tip_angle = 0

        for finger_type in (
            FingerType.RING,
            FingerType.LITTLE,
        ):

            finger = hand.get_finger(
                finger_type
            )

            if finger:
                finger.base_angle = 80
                finger.middle_angle = 80
                finger.tip_angle = 80

        return self.success(
            hand,
            "peace pose created",
        )
