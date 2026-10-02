# validation/validation_result.py

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ValidationIssue:
    """
    バリデーションで発見された1つの問題。
    """

    code: str
    message: str
    severity: str = "warning"
    target: str = ""
    value: Any = None
    expected: Any = None
    repairable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "target": self.target,
            "value": self.value,
            "expected": self.expected,
            "repairable": self.repairable,
        }


@dataclass
class ValidationResult:
    """
    Validator共通の結果。
    """

    valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    def add_issue(
        self,
        code: str,
        message: str,
        severity: str = "warning",
        target: str = "",
        value: Any = None,
        expected: Any = None,
        repairable: bool = True,
    ) -> None:

        self.issues.append(
            ValidationIssue(
                code=code,
                message=message,
                severity=severity,
                target=target,
                value=value,
                expected=expected,
                repairable=repairable,
            )
        )

        if severity == "error":
            self.valid = False

    def add_error(
        self,
        code: str,
        message: str,
        target: str = "",
        value: Any = None,
        expected: Any = None,
        repairable: bool = True,
    ) -> None:

        self.add_issue(
            code=code,
            message=message,
            severity="error",
            target=target,
            value=value,
            expected=expected,
            repairable=repairable,
        )

    def add_warning(
        self,
        code: str,
        message: str,
        target: str = "",
        value: Any = None,
        expected: Any = None,
        repairable: bool = True,
    ) -> None:

        self.add_issue(
            code=code,
            message=message,
            severity="warning",
            target=target,
            value=value,
            expected=expected,
            repairable=repairable,
        )

    @property
    def errors(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "warning"
        ]

    @property
    def repairable_issues(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.repairable
        ]

    def merge(self, other: "ValidationResult") -> None:

        self.issues.extend(other.issues)

        if not other.valid:
            self.valid = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "repairable_count": len(self.repairable_issues),
        }
