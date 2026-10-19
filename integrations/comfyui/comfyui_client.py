# integrations/comfyui/comfyui_client.py

from __future__ import annotations

import json
import logging
import time
import uuid

from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import (
    Request,
    urlopen,
)

logger = logging.getLogger(__name__)


class ComfyUIError(RuntimeError):
    """ComfyUIとの通信または生成処理に関するエラー。"""


class ComfyUIClient:
    """
    ComfyUI HTTP APIクライアント。

    主な機能:
        - 接続確認
        - ワークフロー投入
        - ジョブ完了待ち
        - 入力画像アップロード
        - 生成画像ダウンロード

    外部ライブラリへの依存を避けるため、urllibを使用する。
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        timeout: float = 30.0,
        poll_interval: float = 1.0,
        max_wait_seconds: float = 600.0,
        output_directory: str = "storage/generated",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = max(1.0, float(timeout))
        self.poll_interval = max(0.2, float(poll_interval))
        self.max_wait_seconds = max(1.0, float(max_wait_seconds))

        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client_id = str(uuid.uuid4())

    # ---------------------------------------------------------
    # HTTP通信
    # ---------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> bytes:
        url = f"{self.base_url}{path}"

        if query:
            url = f"{url}?{urlencode(query)}"

        request_headers = dict(headers or {})
        body = data

        if json_body is not None:
            body = json.dumps(
                json_body,
                ensure_ascii=False,
            ).encode("utf-8")

            request_headers["Content-Type"] = "application/json"

        request = Request(
            url=url,
            data=body,
            headers=request_headers,
            method=method.upper(),
        )

        try:
            with urlopen(
                request,
                timeout=timeout or self.timeout,
            ) as response:
                return response.read()

        except HTTPError as exc:
            detail = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise ComfyUIError(
                f"ComfyUI HTTPエラー: "
                f"status={exc.code}, path={path}, detail={detail[:1000]}"
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise ComfyUIError(
                f"ComfyUIへの接続に失敗しました: {path}: {exc}"
            ) from exc

    def _request_json(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raw = self._request(
            method,
            path,
            **kwargs,
        )

        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyUIError(
                f"ComfyUIから不正なJSONが返されました: {path}"
            ) from exc

        if not isinstance(result, dict):
            raise ComfyUIError(
                f"ComfyUIのJSON形式が不正です: {path}"
            )

        return result

    # ---------------------------------------------------------
    # 接続確認
    # ---------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """
        ComfyUIのシステム統計APIに接続できるか確認する。
        """
        try:
            system_stats = self._request_json(
                "GET",
                "/system_stats",
            )

            return {
                "success": True,
                "base_url": self.base_url,
                "system_stats": system_stats,
                "error": None,
            }

        except ComfyUIError as exc:
            return {
                "success": False,
                "base_url": self.base_url,
                "system_stats": None,
                "error": str(exc),
            }

    # ---------------------------------------------------------
    # ワークフロー実行
    # ---------------------------------------------------------

    def queue_prompt(
        self,
        workflow: dict[str, Any],
    ) -> str:
        """
        ワークフローをキューに登録し、prompt_idを取得する。
        """
        if not isinstance(workflow, dict) or not workflow:
            raise ComfyUIError(
                "空のワークフローは実行できません。"
            )

        response = self._request_json(
            "POST",
            "/prompt",
            json_body={
                "prompt": workflow,
                "client_id": self.client_id,
            },
        )

        prompt_id = response.get("prompt_id")

        if not prompt_id:
            raise ComfyUIError(
                "ComfyUIからprompt_idが返されませんでした。"
            )

        return str(prompt_id)

    def get_history(
        self,
        prompt_id: str,
    ) -> dict[str, Any]:
        """
        指定したprompt_idの履歴を取得する。
        """
        return self._request_json(
            "GET",
            f"/history/{prompt_id}",
        )

    def wait_for_completion(
        self,
        prompt_id: str,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """
        ジョブが完了するまで履歴を確認する。

        WebSocketを使用せず、履歴APIを定期的にポーリングする。
        """
        wait_limit = min(
            max(1.0, timeout_seconds or self.max_wait_seconds),
            self.max_wait_seconds,
        )

        deadline = time.monotonic() + wait_limit

        while time.monotonic() < deadline:
            history = self.get_history(prompt_id)

            job = history.get(prompt_id)

            if isinstance(job, dict):
                status = job.get("status", {})

                if isinstance(status, dict):
                    status_str = str(
                        status.get("status_str", "")
                    ).lower()

                    if (
                        status.get("completed") is True
                        or status_str == "success"
                    ):
                        return job

                    if status.get("status_str") == "error":
                        raise ComfyUIError(
                            f"画像生成ジョブが失敗しました: {prompt_id}"
                        )

                # 環境やバージョンによってstatusの形式が
                # 異なる場合があるため、outputsも確認する。
                outputs = job.get("outputs")

                if isinstance(outputs, dict) and outputs:
                    return job

            time.sleep(self.poll_interval)

        raise ComfyUIError(
            f"画像生成がタイムアウトしました: "
            f"prompt_id={prompt_id}, timeout={wait_limit}"
        )

    # ---------------------------------------------------------
    # 画像アップロード
    # ---------------------------------------------------------

    def upload_image(
        self,
        image_path: str,
        *,
        subfolder: str = "inputs",
        image_type: str = "input",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """
        ComfyUIの入力画像アップロードAPIを使用する。

        戻り値のname/subfolder/typeを、
        ワークフローのLoadImageノードへ渡す。
        """
        path = Path(image_path)

        if not path.is_file():
            raise ComfyUIError(
                f"アップロード対象の画像が存在しません: {path}"
            )

        allowed_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".bmp",
        }

        if path.suffix.lower() not in allowed_extensions:
            raise ComfyUIError(
                f"未対応の画像形式です: {path.suffix}"
            )

        boundary = f"----ComfyUIBoundary{uuid.uuid4().hex}"

        file_bytes = path.read_bytes()

        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                (
                    "Content-Disposition: form-data; "
                    f'name="image"; filename="{path.name}"\r\n'
                ).encode(),
                b"Content-Type: application/octet-stream\r\n\r\n",
                file_bytes,
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; '
                    'name="subfolder"\r\n\r\n'
                ).encode(),
                subfolder.encode("utf-8"),
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; '
                    'name="type"\r\n\r\n'
                ).encode(),
                image_type.encode("utf-8"),
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; '
                    'name="overwrite"\r\n\r\n'
                ).encode(),
                str(overwrite).lower().encode(),
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )

        raw = self._request(
            "POST",
            "/upload/image",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )

        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyUIError(
                "画像アップロードの応答を解析できません。"
            ) from exc

        if not isinstance(response, dict) or not response.get("name"):
            raise ComfyUIError(
                f"画像アップロードに失敗しました: {response}"
            )

        return response

    # ---------------------------------------------------------
    # 生成画像の取得
    # ---------------------------------------------------------

    def download_image(
        self,
        image_info: dict[str, Any],
        *,
        prefix: str = "generated",
    ) -> str:
        """
        ComfyUIの画像取得APIから画像を保存する。
        """
        filename = Path(
            str(image_info.get("filename", ""))
        ).name

        if not filename:
            raise ComfyUIError(
                "生成画像のファイル名がありません。"
            )

        image_type = str(
            image_info.get("type", "output")
        )

        if image_type not in {"output", "temp", "input"}:
            raise ComfyUIError(
                f"不正な画像タイプです: {image_type}"
            )

        subfolder = str(
            image_info.get("subfolder", "")
        )

        if Path(subfolder).is_absolute() or ".." in Path(subfolder).parts:
            raise ComfyUIError(
                "不正な画像サブフォルダーです。"
            )

        raw = self._request(
            "GET",
            "/view",
            query={
                "filename": filename,
                "subfolder": subfolder,
                "type": image_type,
            },
        )

        extension = Path(filename).suffix.lower()

        if extension not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            extension = ".png"

        output_name = f"{prefix}_{uuid.uuid4().hex}{extension}"

        output_path = (
            self.output_directory / output_name
        ).resolve()

        output_root = self.output_directory.resolve()

        if not output_path.is_relative_to(output_root):
            raise ComfyUIError(
                "保存先が出力ディレクトリの外側です。"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_bytes(raw)

        return str(output_path)

    # ---------------------------------------------------------
    # 一連の生成処理
    # ---------------------------------------------------------

    def generate(
        self,
        workflow: dict[str, Any],
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """
        ワークフロー投入から画像保存まで実行する。
        """
        prompt_id = self.queue_prompt(workflow)

        job = self.wait_for_completion(
            prompt_id,
            timeout_seconds=timeout_seconds,
        )

        outputs = job.get("outputs", {})

        if not isinstance(outputs, dict):
            raise ComfyUIError(
                "生成ジョブに有効なoutputsがありません。"
            )

        saved_images: list[str] = []

        for node_id, node_output in outputs.items():
            if not isinstance(node_output, dict):
                continue

            images = node_output.get("images", [])

            if not isinstance(images, list):
                continue

            for image_index, image_info in enumerate(images):
                if not isinstance(image_info, dict):
                    continue

                saved_path = self.download_image(
                    image_info,
                    prefix=f"{prompt_id}_{node_id}_{image_index}",
                )

                saved_images.append(saved_path)

        if not saved_images:
            raise ComfyUIError(
                "生成ジョブは完了しましたが、画像出力が見つかりません。"
            )

        return {
            "success": True,
            "prompt_id": prompt_id,
            "images": saved_images,
            "job": job,
        }
