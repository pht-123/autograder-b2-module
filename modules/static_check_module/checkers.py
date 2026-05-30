from __future__ import annotations

import ast
import subprocess
from models.submission import StaticIssue


import subprocess

class SyntaxChecker:
    def check(self, code: str, language: str = "python") -> list[StaticIssue]:
        if language == "python":
            return self._check_python(code)
        elif language == "shell":
            return self._check_shell(code)
        return []

    def _check_shell(self, code: str) -> list[StaticIssue]:
        try:
            # 使用 bash -n 进行静态语法检查
            result = subprocess.run(
                ["bash", "-n"], input=code, text=True,
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return []
            # 解析 bash -n 的错误输出获取行号和信息
            return [StaticIssue(
                type="syntax",
                message=result.stderr.strip() or "shell syntax error",
                line=None, # bash -n 错误信息中提取行号较复杂，可暂设为 None
            )]
        except FileNotFoundError:
            return [StaticIssue(type="syntax", message="bash interpreter not found", line=None)]
        except subprocess.TimeoutExpired:
            return [StaticIssue(type="syntax", message="shell syntax check timeout", line=None)]



class ForbiddenChecker:
    def check(
        self,
        code: str,
        forbidden_modules: list[str] | None,
        forbidden_functions: list[str] | None,
        allowed_commands: list[str] | None = None,
        language: str = "python",
    ) -> list[StaticIssue]:
        if language == "python":  # 仅在 Python 中进行禁止模块和函数的检查
            return self._check_python(code, forbidden_modules, forbidden_functions)
        elif language == "shell":
            return self._check_shell_commands(code, allowed_commands or [])
        return []

    def _check_python(self, code: str, forbidden_modules: list[str] | None, forbidden_functions: list[str] | None) -> list[StaticIssue]:
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

    def _check_shell_commands(self, code: str, allowed_commands: list[str]) -> list[StaticIssue]:
        issues = []
        for line_num, line in enumerate(code.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            cmd = stripped.split()[0]
            if cmd not in allowed_commands:
                issues.append(
                    StaticIssue(
                        type="forbidden",
                        message=f"使用了不允许的命令: {cmd}",
                        line=line_num,
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

