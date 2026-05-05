from __future__ import annotations

import ast

from models.submission import StaticIssue


class SyntaxChecker:
    def check(self, code: str) -> list[StaticIssue]:
        try:
            ast.parse(code)
            return []
        except SyntaxError as exc:
            return [
                StaticIssue(
                    type="syntax",
                    message=str(exc).strip() or "syntax error",
                    line=getattr(exc, "lineno", None),
                )
            ]


class ForbiddenChecker:
    def check(
        self,
        code: str,
        forbidden_modules: list[str] | None,
        forbidden_functions: list[str] | None,
    ) -> list[StaticIssue]:
        forbidden_modules = [m for m in (forbidden_modules or []) if m]
        forbidden_functions = [f for f in (forbidden_functions or []) if f]

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Syntax errors are handled by SyntaxChecker; skip further analysis.
            return []

        issues: list[StaticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if name in forbidden_modules:
                        issues.append(
                            StaticIssue(
                                type="forbidden",
                                message=f"使用了禁止模块 {name}",
                                line=getattr(node, "lineno", None),
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    name = node.module.split(".")[0]
                    if name in forbidden_modules:
                        issues.append(
                            StaticIssue(
                                type="forbidden",
                                message=f"使用了禁止模块 {name}",
                                line=getattr(node, "lineno", None),
                            )
                        )
            elif isinstance(node, ast.Call):
                fn_name = _call_name(node.func)
                if fn_name and fn_name in forbidden_functions:
                    issues.append(
                        StaticIssue(
                            type="forbidden",
                            message=f"使用了禁止函数 {fn_name}",
                            line=getattr(node, "lineno", None),
                        )
                    )
        return issues


def _call_name(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        # a.b() -> "b" (function-level blacklist)
        return expr.attr
    return None

