# Issue #24 — Verification Report

## Acceptance Criteria
- ✅ Errors parsed into `{line, column, message}` — implemented in `backend/app/errors.py` (`CompileError` dataclass + `parse_compile_errors()` function)
- ✅ Error phase identified (lexer, parser, semantic) — `_infer_phase()` in `errors.py` detects phase from error text

## Implementation Details

### `backend/app/errors.py`
- `CompileError` dataclass with fields: `phase: str`, `line: int`, `column: int`, `message: str`
- `parse_compile_errors(stderr: str) -> list[CompileError]` parses simplesc stderr output
- Regex patterns for lexer, parser, semantic errors (case-insensitive, Portuguese keywords: `erro lexico`, `erro sintatico`, `erro semantico`)
- Generic fallback pattern for unrecognized formats

### `backend/app/compiler.py`
- `_run_simplesc()` calls `parse_compile_errors(proc.stderr)` on non-zero exit codes

### `backend/app/ws_handler.py`
- `_handle_compile_and_run()` sends structured `compile_error` messages with `{errors: [{phase, line, column, message}]}`

### Tests
- 12 tests in `backend/tests/test_errors.py` (all passing)
- 9 tests in `backend/tests/test_compiler.py` (all passing)

## Verification
```bash
cd backend
python -m pytest tests/test_errors.py tests/test_compiler.py -v
# Result: 21 passed in 0.03s
```
