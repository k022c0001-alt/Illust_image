# integrations/comfyui/workflow_registry.py

from __future__ import annotations

import json

from pathlib import Path
from typing import Any


class WorkflowRegistryError(RuntimeError):
    """ワークフローの読み込み・登録エラー。"""


class WorkflowRegistry:
    """
    ComfyUIワークフローJSONを管理する。

    ワークフローJSONと、Python側から操作するノードの対応表を
    別々に管理する。
    """

    def __init__(
        self,
        workflow_directory: str = "integrations/comfyui/workflows",
    ) -> None:
        self.workflow_directory = Path(workflow_directory)
        self._definitions: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        definition: dict[str, Any],
    ) -> None:
        if not name or not name.strip():
            raise WorkflowRegistryError(
                "ワークフロー名を指定してください。"
            )

        if not isinstance(definition, dict):
            raise WorkflowRegistryError(
                "ワークフロー定義は辞書形式で指定してください。"
            )

        workflow_file = definition.get("workflow_file")
        node_map = definition.get("node_map")

        if not isinstance(workflow_file, str) or not workflow_file:
            raise WorkflowRegistryError(
                f"{name}: workflow_file がありません。"
            )

        if not isinstance(node_map, dict):
            raise WorkflowRegistryError(
                f"{name}: node_map がありません。"
            )

        self._definitions[name] = definition

    def get_definition(
        self,
        name: str,
    ) -> dict[str, Any]:
        if name not in self._definitions:
            raise WorkflowRegistryError(
                f"未登録のワークフローです: {name}"
            )

        return dict(self._definitions[name])

    def load_workflow(
        self,
        name: str,
    ) -> dict[str, Any]:
        definition = self.get_definition(name)

        filename = Path(definition["workflow_file"])

        if filename.is_absolute() or ".." in filename.parts:
            raise WorkflowRegistryError(
                "ワークフローのパスが不正です。"
            )

        workflow_path = (
            self.workflow_directory / filename
        ).resolve()

        root = self.workflow_directory.resolve()

        if not workflow_path.is_relative_to(root):
            raise WorkflowRegistryError(
                "ワークフローが許可されたディレクトリ外を参照しています。"
            )

        if not workflow_path.is_file():
            raise WorkflowRegistryError(
                f"ワークフローJSONがありません: {workflow_path}"
            )

        try:
            workflow = json.loads(
                workflow_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise WorkflowRegistryError(
                f"JSONの形式が不正です: {workflow_path}"
            ) from exc

        if not isinstance(workflow, dict) or not workflow:
            raise WorkflowRegistryError(
                f"ワークフローが空、または辞書形式ではありません: "
                f"{workflow_path}"
            )

        return workflow

    def list_workflows(self) -> list[str]:
        return sorted(self._definitions.keys())
