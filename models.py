from typing import Any, Dict


class CompilerError:
    """
    Structured representation of a compiler error detected during analysis.

    This is intentionally simple and framework‑agnostic so you can reuse it
    in different analyzers or resolvers without depending on FastAPI/Pydantic.
    """

    def __init__(
        self,
        type: str,
        code: str,
        message: str,
        line: int,
        column: int,
        hint: str,
    ) -> None:
        self.type = type
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        self.hint = hint

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error into a plain dict, ready to be JSON‑encoded
        and consumed by the React frontend.
        """
        return {
            "type": self.type,
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "hint": self.hint,
        }

