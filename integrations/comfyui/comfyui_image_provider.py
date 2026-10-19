# integrations/comfyui/comfyui_image_provider.py

from __future__ import annotations

import logging

from pathlib import Path
from typing import Any

from ai.image.generation_config import GenerationConfig
from ai.image.generation_request import GenerationRequest
from ai.image.generation_result import GenerationResult
from ai.image.image_generation_provider import ImageGenerationProvider

from integrations.comfyui.comfyui_client import (
    ComfyUIClient,
    ComfyUIError,
)
from integrations.comfyui.workflow_builder import (
    WorkflowBuilder,
    WorkflowBuildError,
)

logger = logging.getLogger(__name__)


class ComfyUIImageProvider(ImageGenerationProvider):
    """
    ComfyUIを使用する画像生成プロバイダー。

    ワークフロー名:
        txt2img
        img2img
        inpaint

    ワークフローごとのノード構成は、WorkflowRegistryで管理する。
    """

    def __init__(
        self,
        client: ComfyUIClient,
        workflow_builder: WorkflowBuilder,
        default_timeout: float = 600.0,
    ) -> None:
        self.client = client
        self.workflow_builder = workflow_builder
        self.default_timeout = max(1.0, default_timeout)

    def health_check(self) -> dict[str, Any]:
        return self.client.health_check()

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        return self._run_workflow(
            workflow_name="txt2img",
            request=request,
        )

    def image_to_image(
        self,
        source_image: str,
        request: GenerationRequest,
    ) -> GenerationResult:
        return self._run_workflow(
            workflow_name="img2img",
            request=request,
            source_image=source_image,
        )

    def inpaint(
        self,
        source_image: str,
        mask_image: str,
        request: GenerationRequest,
    ) -> GenerationResult:
        return self._run_workflow(
            workflow_name="inpaint",
            request=request,
            source_image=source_image,
            mask_image=mask_image,
        )

    def _run_workflow(
        self,
        workflow_name: str,
        request: GenerationRequest,
        source_image: str | None = None,
        mask_image: str | None = None,
    ) -> GenerationResult:
        try:
            config = request.config

            values = self._build_values(
                config=config,
                request=request,
            )

            # 元画像をComfyUIへアップロードする。
            if source_image:
                if not Path(source_image).is_file():
                    raise ComfyUIError(
                        f"元画像が存在しません: {source_image}"
                    )

                uploaded = self.client.upload_image(
                    source_image,
                )

                values.update(
                    self._image_upload_values(
                        "source",
                        uploaded,
                    )
                )

            # マスク画像をアップロードする。
            if mask_image:
                if not Path(mask_image).is_file():
                    raise ComfyUIError(
                        f"マスク画像が存在しません: {mask_image}"
                    )

                uploaded_mask = self.client.upload_image(
                    mask_image,
                )

                values.update(
                    self._image_upload_values(
                        "mask",
                        uploaded_mask,
                    )
                )

            workflow = self.workflow_builder.build(
                workflow_name=workflow_name,
                values=values,
            )

            self.workflow_builder.validate_workflow(
                workflow
            )

            result = self.client.generate(
                workflow,
                timeout_seconds=self.default_timeout,
            )

            images = result.get("images", [])

            if not images:
                raise ComfyUIError(
                    "生成結果に画像がありません。"
                )

            return GenerationResult(
                success=True,
                image_path=images[0],
                seed=getattr(config, "seed", None),
                model_name=getattr(config, "model_name", None),
                message="ComfyUIによる画像生成が完了しました。",
                errors=[],
                metadata={
                    "provider": "comfyui",
                    "workflow": workflow_name,
                    "prompt_id": result.get("prompt_id"),
                    "images": images,
                },
            )

        except (
            ComfyUIError,
            WorkflowBuildError,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            logger.exception(
                "ComfyUIの画像生成に失敗しました: %s",
                workflow_name,
            )

            return GenerationResult(
                success=False,
                image_path=None,
                seed=getattr(request.config, "seed", None),
                model_name=getattr(
                    request.config,
                    "model_name",
                    None,
                ),
                message=f"ComfyUIの画像生成に失敗しました: {exc}",
                errors=[str(exc)],
                metadata={
                    "provider": "comfyui",
                    "workflow": workflow_name,
                },
            )

    @staticmethod
    def _build_values(
        config: GenerationConfig,
        request: GenerationRequest,
    ) -> dict[str, Any]:
        """
        生成設定をワークフローに渡す値へ変換する。

        モデルごとの設定変換が必要な場合は、
        この部分を拡張する。
        """
        prompt = (
            request.prompt
            or getattr(config, "prompt", "")
            or ""
        )

        negative_prompt = (
            request.negative_prompt
            or getattr(config, "negative_prompt", "")
            or ""
        )

        values = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": int(config.width),
            "height": int(config.height),
            "steps": int(config.steps),
            "cfg": float(config.guidance_scale),
            "seed": int(config.seed),
            "checkpoint": config.model_name,
        }

        # Noneのモデル名をワークフローに渡さない。
        if not values["checkpoint"]:
            values.pop("checkpoint")

        # 対応するワークフローだけが利用する追加値。
        if getattr(config, "lora_name", None):
            values["lora_name"] = config.lora_name

        if getattr(config, "lora_strength", None) is not None:
            values["lora_strength"] = float(
                config.lora_strength
            )

        if getattr(config, "denoise_strength", None) is not None:
            values["denoise"] = float(
                config.denoise_strength
            )

        values.update(
            getattr(config, "control_weights", {}) or {}
        )

        return values

    @staticmethod
    def _image_upload_values(
        prefix: str,
        upload_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        アップロード結果をワークフロー用の値に変換する。
        """
        name = upload_result.get("name")

        if not name:
            raise ComfyUIError(
                "アップロード結果に画像名がありません。"
            )

        subfolder = upload_result.get("subfolder", "")
        image_type = upload_result.get("type", "input")

        return {
            f"{prefix}_image": name,
            f"{prefix}_subfolder": subfolder,
            f"{prefix}_type": image_type,
        }
