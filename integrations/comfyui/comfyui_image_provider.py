# -*- coding: utf-8 -*-
"""
ComfyUIImageProvider.py

ComfyUIを使ったローカル画像生成プロバイダー。

対応する処理:
- txt2img: テキストから画像を生成
- img2img: 既存画像を参考に画像を生成
- inpaint: マスク領域を修正

注意:
ワークフローJSONのノードIDと入力名は、
使用するComfyUIワークフローに合わせて設定すること。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ai.image.generation_request import GenerationRequest
from ai.image.generation_result import GenerationResult
from ai.image.image_generation_provider import ImageGenerationProvider

from integrations.comfyui.comfyui_client import ComfyUIClient
from integrations.comfyui.workflow_builder import WorkflowBuilder


class ComfyUIImageProvider(ImageGenerationProvider):
    """ComfyUIを既存の画像生成インターフェースに接続する。"""

    def __init__(
        self,
        client: ComfyUIClient,
        workflow_builder: WorkflowBuilder,
        output_dir: str | Path = "storage/generated",
        default_workflow: str = "txt2img",
    ) -> None:
        self.client = client
        self.workflow_builder = workflow_builder
        self.output_dir = Path(output_dir)
        self.default_workflow = default_workflow

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> bool:
        """ComfyUIに接続できるかを確認する。"""
        try:
            result = self.client.health_check()

            # クライアントの実装差を吸収する。
            if isinstance(result, bool):
                return result

            if isinstance(result, dict):
                return bool(result.get("success", False))

            return bool(result)

        except Exception:
            return False

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """テキストから画像を生成する。"""
        return self._run_workflow(
            workflow_name="txt2img",
            request=request,
        )

    def image_to_image(
        self,
        source_image: str | Path,
        request: GenerationRequest,
    ) -> GenerationResult:
        """既存画像を参考に画像を生成する。"""
        source = Path(source_image)

        if not source.is_file():
            return self._failure(
                message="img2imgの元画像が見つかりません。",
                errors=[f"source_image_not_found: {source}"],
            )

        return self._run_workflow(
            workflow_name="img2img",
            request=request,
            source_image=source,
        )

    def inpaint(
        self,
        source_image: str | Path,
        mask_image: str | Path,
        request: GenerationRequest,
    ) -> GenerationResult:
        """マスク領域を中心に画像を修正する。"""
        source = Path(source_image)
        mask = Path(mask_image)

        missing = []

        if not source.is_file():
            missing.append(f"source_image_not_found: {source}")

        if not mask.is_file():
            missing.append(f"mask_image_not_found: {mask}")

        if missing:
            return self._failure(
                message="inpaintに必要なファイルがありません。",
                errors=missing,
            )

        return self._run_workflow(
            workflow_name="inpaint",
            request=request,
            source_image=source,
            mask_image=mask,
        )

    def _run_workflow(
        self,
        workflow_name: str,
        request: GenerationRequest,
        source_image: Optional[Path] = None,
        mask_image: Optional[Path] = None,
    ) -> GenerationResult:
        """ワークフローの構築から画像保存までを実行する。"""

        try:
            config = request.config

            values: dict[str, Any] = {
                "prompt": (
                    request.prompt
                    or getattr(config, "prompt", "")
                    or ""
                ),
                "negative_prompt": (
                    request.negative_prompt
                    or getattr(config, "negative_prompt", "")
                    or ""
                ),
                "width": getattr(config, "width", 1024),
                "height": getattr(config, "height", 1024),
                "steps": getattr(config, "steps", 25),
                "cfg": getattr(config, "guidance_scale", 7.0),
                "seed": getattr(config, "seed", -1),
                "denoise": getattr(config, "denoise_strength", 0.65),
                "checkpoint": getattr(config, "model_name", ""),
                "lora_name": getattr(config, "lora_name", ""),
                "lora_strength": getattr(config, "lora_strength", 1.0),
            }

            # 既存の条件をワークフローに渡す。
            # ワークフロー側に対応するマッピングがある場合のみ反映される。
            conditions = getattr(request, "conditions", None)

            if isinstance(conditions, dict):
                values["conditions"] = conditions

            metadata = getattr(request, "metadata", None)

            if isinstance(metadata, dict):
                values["metadata"] = metadata

            # 元画像・マスクをComfyUIへアップロードする。
            if source_image is not None:
                uploaded_source = self.client.upload_image(
                    source_image
                )
                values["source_image"] = self._uploaded_name(
                    uploaded_source
                )

            if mask_image is not None:
                uploaded_mask = self.client.upload_image(
                    mask_image
                )
                values["mask_image"] = self._uploaded_name(
                    uploaded_mask
                )

            # WorkflowBuilderが論理名からノード入力へ変換する。
            workflow = self.workflow_builder.build(
                workflow_name=workflow_name,
                values=values,
            )

            validation_errors = (
                self.workflow_builder.validate_workflow(workflow)
            )

            if validation_errors:
                return self._failure(
                    message="ワークフローの検証に失敗しました。",
                    errors=[str(error) for error in validation_errors],
                    metadata={"workflow_name": workflow_name},
                )

            result = self.client.generate(workflow)

            if not isinstance(result, dict):
                return self._failure(
                    message="ComfyUIから不正な形式の結果が返されました。",
                    errors=["invalid_comfyui_result"],
                )

            if not result.get("success"):
                return self._failure(
                    message=str(
                        result.get("message", "画像生成に失敗しました。")
                    ),
                    errors=[
                        str(error)
                        for error in result.get("errors", [])
                    ],
                    metadata={
                        "workflow_name": workflow_name,
                        "comfyui_result": result,
                    },
                )

            images = result.get("images", [])

            if not images:
                return self._failure(
                    message="生成処理は終了しましたが、画像がありません。",
                    errors=["generated_image_missing"],
                    metadata={
                        "workflow_name": workflow_name,
                        "prompt_id": result.get("prompt_id"),
                    },
                )

            # 現時点では最初の出力画像を採用する。
            first_image = images[0]

            image_path = (
                first_image.get("path")
                if isinstance(first_image, dict)
                else first_image
            )

            if not image_path:
                return self._failure(
                    message="生成画像の保存先を取得できませんでした。",
                    errors=["generated_image_path_missing"],
                )

            image_path = Path(image_path)

            if not image_path.is_file():
                return self._failure(
                    message="生成画像のファイルが見つかりません。",
                    errors=[f"generated_file_not_found: {image_path}"],
                )

            return GenerationResult(
                success=True,
                image_path=str(image_path),
                seed=values["seed"],
                model_name=values["checkpoint"],
                message="画像生成に成功しました。",
                errors=[],
                metadata={
                    "workflow_name": workflow_name,
                    "prompt_id": result.get("prompt_id"),
                    "source_image": (
                        str(source_image)
                        if source_image is not None
                        else None
                    ),
                    "mask_image": (
                        str(mask_image)
                        if mask_image is not None
                        else None
                    ),
                    "comfyui_metadata": result.get("metadata", {}),
                },
            )

        except Exception as exc:
            # ワークフロー未登録、接続失敗、HTTPエラーなどを
            # GenerationResultに変換する。
            return self._failure(
                message=f"{workflow_name}の実行に失敗しました。",
                errors=[
                    f"{type(exc).__name__}: {exc}"
                ],
                metadata={"workflow_name": workflow_name},
            )

    @staticmethod
    def _uploaded_name(upload_result: Any) -> str:
        """アップロード結果からLoadImage等に渡す名前を取り出す。"""

        if isinstance(upload_result, str):
            return upload_result

        if isinstance(upload_result, dict):
            name = upload_result.get("name")

            if name:
                subfolder = upload_result.get("subfolder", "")

                if subfolder:
                    return f"{subfolder}/{name}"

                return str(name)

        raise ValueError(
            "ComfyUIのアップロード結果から画像名を取得できません。"
        )

    @staticmethod
    def _failure(
        message: str,
        errors: list[str],
        metadata: Optional[dict[str, Any]] = None,
    ) -> GenerationResult:
        return GenerationResult(
            success=False,
            image_path=None,
            seed=None,
            model_name=None,
            message=message,
            errors=errors,
            metadata=metadata or {},
        )
