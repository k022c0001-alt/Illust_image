# -*- coding: utf-8 -*-
"""
character_model.py

画像生成・アニメーションで使用する
キャラクターの基本情報を定義します。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BodyProportion:
    """
    キャラクターの身体比率。

    画像生成時に腕・足・頭身などが
    大きく崩れないようにするための基準値。
    """

    total_height: float = 1.0

    head_height: float = 0.14
    neck_length: float = 0.04

    shoulder_width: float = 0.22
    chest_width: float = 0.20
    waist_width: float = 0.14
    hip_width: float = 0.20

    upper_arm_length: float = 0.16
    forearm_length: float = 0.15

    upper_leg_length: float = 0.25
    lower_leg_length: float = 0.24

    hand_length: float = 0.08
    foot_length: float = 0.12


@dataclass
class CharacterAppearance:
    """
    キャラクターの外見情報。
    """

    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    skin_color: Optional[str] = None

    clothing: List[str] = field(default_factory=list)
    accessories: List[str] = field(default_factory=list)

    description: str = ""


@dataclass
class CharacterModel:
    """
    アニメーション対象となるキャラクター。

    「元画像」だけでなく、
    キャラクターを構成する情報を保持します。
    """

    character_id: str

    name: str = ""

    source_image: Optional[str] = None

    body: BodyProportion = field(
        default_factory=BodyProportion
    )

    appearance: CharacterAppearance = field(
        default_factory=CharacterAppearance
    )

    style_id: Optional[str] = None

    reference_images: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, object] = field(
        default_factory=dict
    )

    def add_reference_image(self, path: str) -> None:
        """キャラクター参考画像を追加する。"""

        if path and path not in self.reference_images:
            self.reference_images.append(path)

    def add_clothing(self, clothing: str) -> None:
        """衣装情報を追加する。"""

        if clothing and clothing not in self.appearance.clothing:
            self.appearance.clothing.append(clothing)

    def add_accessory(self, accessory: str) -> None:
        """アクセサリー情報を追加する。"""

        if accessory and accessory not in self.appearance.accessories:
            self.appearance.accessories.append(accessory)

    def get_body_ratio(self, name: str) -> Optional[float]:
        """
        身体比率を取得する。
        """

        return getattr(self.body, name, None)

    def to_dict(self) -> Dict[str, object]:
        """JSON保存用データへ変換する。"""

        return {
            "character_id": self.character_id,
            "name": self.name,
            "source_image": self.source_image,
            "body": vars(self.body),
            "appearance": vars(self.appearance),
            "style_id": self.style_id,
            "reference_images": self.reference_images,
            "metadata": self.metadata,
        }
