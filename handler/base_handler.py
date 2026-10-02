# -*- coding: utf-8 -*-
"""
base_handler.py

画像アニメーションAI用Handlerの基底クラス。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class HandlerResult:
    """
    Handlerの処理結果。
    """

    def __init__(
        self,
        success: bool,
        data: Any = None,
        message: str = "",
        errors: Optional[list[str]] = None,
    ):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "errors": self.errors,
        }


class BaseHandler(ABC):
    """
    全Handlerの基底クラス。
    """

    name = "base"

    def __init__(self):
        self.last_result: Optional[HandlerResult] = None

    @abstractmethod
    def handle(
        self,
        request: Dict[str, Any],
    ) -> HandlerResult:
        """
        Handler本体。
        """
        raise NotImplementedError

    def success(
        self,
        data: Any = None,
        message: str = "",
    ) -> HandlerResult:

        result = HandlerResult(
            success=True,
            data=data,
            message=message,
        )

        self.last_result = result

        return result

    def failure(
        self,
        message: str,
        errors: Optional[list[str]] = None,
    ) -> HandlerResult:

        result = HandlerResult(
            success=False,
            message=message,
            errors=errors or [],
        )

        self.last_result = result

        return result

    def require(
        self,
        request: Dict[str, Any],
        key: str,
    ) -> Any:

        value = request.get(key)

        if value is None:
            raise ValueError(
                f"required field is missing: {key}"
            )

        return value
