# repair/face_repair.py

from api.services.models.face_model import FaceModel

from .repair_result import RepairResult


class FaceRepair:
    """
    FaceModelの異常値を修正する。
    """

    EXPRESSIONS = {
        "neutral",
        "smile",
        "sad",
        "angry",
        "surprised",
        "happy",
        "serious",
    }

    def repair(
        self,
        face: FaceModel,
    ) -> RepairResult:

        result = RepairResult()

        if face is None:

            result.success = False

            result.add_warning(
                "FaceModelが存在しないため修正できません。"
            )

            return result

        self._clamp(
            face,
            result,
            "head_rotation_x",
            -90,
            90,
        )

        self._clamp(
            face,
            result,
            "head_rotation_y",
            -120,
            120,
        )

        self._clamp(
            face,
            result,
            "head_rotation_z",
            -60,
            60,
        )

        self._clamp(
            face,
            result,
            "eye_direction_x",
            -1,
            1,
        )

        self._clamp(
            face,
            result,
            "eye_direction_y",
            -1,
            1,
        )

        self._clamp(
            face,
            result,
            "mouth_open",
            0,
            1,
        )

        self._clamp(
            face,
            result,
            "mouth_curve",
            -1,
            1,
        )

        if (
            face.expression
            and face.expression not in self.EXPRESSIONS
        ):

            before = face.expression

            face.expression = "neutral"

            result.add_action(
                target="expression",
                action="replace",
                before=before,
                after="neutral",
                reason="未登録の表情だったため",
            )

        return result

    def _clamp(
        self,
        obj,
        result,
        field_name,
        minimum,
        maximum,
    ):

        value = getattr(obj, field_name)

        repaired = max(
            minimum,
            min(maximum, value),
        )

        if repaired == value:
            return

        setattr(
            obj,
            field_name,
            repaired,
        )

        result.add_action(
            target=field_name,
            action="clamp",
            before=value,
            after=repaired,
            reason="許容範囲を超えていたため",
        )
