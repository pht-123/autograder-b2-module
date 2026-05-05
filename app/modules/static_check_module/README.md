# StaticCheckModule

## Purpose
Run static checks without executing code:
- Python syntax validity (AST parse)
- Forbidden module / function scan

## Inputs
- `submitted_code` (string)
- forbidden rules from B3:
  - `forbidden_modules[]`
  - `forbidden_functions[]`

## Outputs
- `static_issues[]` with `type/message/line`

## Implementation
- [checkers.py](file:///Users/bytedance/Desktop/作业/b2_project/app/modules/static_check_module/checkers.py)

