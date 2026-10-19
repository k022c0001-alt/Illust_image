# integrations/comfyui/workflow_builder.py

from __future__ import annotations

import copy

from typing import Any

from integrations.comfyui.workflow_registry import (
    WorkflowRegistry,
    WorkflowRegistryError,
)


class WorkflowBuildError(RuntimeError):
    """ワークフロー構築時のエラー。"""


class WorkflowBuilder:
    """
    登録済みのワークフローへ生成条件を反映する。

    node_map の例:
    {
        "checkpoint": {
            "node_id": "4",
            "inputs": {
                "ckpt_name": "model_name"
            }
        },
        "positive_prompt": {
            "node_id": "6",
            "inputs": {
                "text": "prompt"
            }
        }
    }

    inputs の右辺は、values辞書のキーを表す。
    """

    def __init__(
        self,
        registry: WorkflowRegistry,
    ) -> None:
        self.registry = registry

    def build(
        self,
        workflow_name: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        workflow = self.registry.load_workflow(
            workflow_name
        )

        definition = self.registry.get_definition(
            workflow_name
        )

        node_map = definition.get("node_map", {})

        if not isinstance(node_map, dict):
            raise WorkflowBuildError(
                "node_map の形式が不正です。"
            )

        # 登録済みJSONを直接変更しない。
        result = copy.deepcopy(workflow)

        for logical_name, mapping in node_map.items():
            if not isinstance(mapping, dict):
                raise WorkflowBuildError(
                    f"{logical_name}: ノード設定が不正です。"
                )

            node_id = str(mapping.get("node_id", ""))

            if not node_id:
                raise WorkflowBuildError(
                    f"{logical_name}: node_id がありません。"
                )

            node = result.get(node_id)

            if not isinstance(node, dict):
                raise WorkflowBuildError(
                    f"{logical_name}: ノード {node_id} がありません。"
                )

            inputs = node.get("inputs")

            if not isinstance(inputs, dict):
                raise WorkflowBuildError(
                    f"{logical_name}: inputs がありません。"
                )

            input_map = mapping.get("inputs", {})

            if not isinstance(input_map, dict):
                raise WorkflowBuildError(
                    f"{logical_name}: inputsの対応表が不正です。"
                )

            for input_name, value_key in input_map.items():
                if value_key not in values:
                    continue

                # 元のワークフローに存在しない入力は
                # 勝手に追加しない。
                if input_name not in inputs:
                    raise WorkflowBuildError(
                        f"{logical_name}: "
                        f"入力 {input_name} がワークフローにありません。"
                    )

                inputs[input_name] = values[value_key]

        return result

    @staticmethod
    def validate_workflow(
        workflow: dict[str, Any],
    ) -> None:
        """
        基本構造を確認する。

        ComfyUIの全ノードの実行可能性を保証する検証ではない。
        """
        if not isinstance(workflow, dict) or not workflow:
            raise WorkflowBuildError(
                "ワークフローが空です。"
            )

        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                raise WorkflowBuildError(
                    f"ノード {node_id} の形式が不正です。"
                )

            if not isinstance(node.get("class_type"), str):
                raise WorkflowBuildError(
                    f"ノード {node_id} に class_type がありません。"
                )

            if not isinstance(node.get("inputs"), dict):
                raise WorkflowBuildError(
                    f"ノード {node_id} に inputs がありません。"
                )
