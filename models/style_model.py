# -*- coding: utf-8 -*-
"""
style_model.py

ユーザー固有の絵柄・描画特徴を管理するModel。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StyleModel:
    """
    絵柄情報。

    実際のAIモデルやLoRAそのものではなく、
    それらを呼び出すための設定情報を保持します。
    """

    style_id: str

    name: str = ""

    reference_images: List[str] = field(
        default_factory=list
    )

    line_weight: float = 0.5

    color_strength: float = 0.5

    shading_strength: float = 0.5

    detail_level: float = 0.5

    style_strength: float = 0.8

    model_name: Optional[str] = None

    lora_name: Optional[str] = None

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    def add_reference_image(
        self,
        path: str
    ) -> None:

        if path and path not in self.reference_images:
            self.reference_images.append(path)

    def set_style_strength(
        self,
        value: float
    ) -> None:

        self.style_strength = max(
            0.0,
            min(1.0, value)
        )

    def to_dict(self) -> Dict[str, object]:

        return vars(self).copy()
