"""Tests for error parsing module (errors.py)."""

from app.errors import parse_compile_errors, CompileError, _infer_phase


class TestParseCompileErrors:
    """Tests for parse_compile_errors()."""

    def test_empty_stderr(self):
        """Empty stderr should return empty list."""
        assert parse_compile_errors("") == []
        assert parse_compile_errors("   \n\n  ") == []

    def test_lexer_error(self):
        """Lexer error should be correctly parsed."""
        stderr = "line 4, col 7: erro lexico: caractere invalido '@'"
        errors = parse_compile_errors(stderr)
        assert len(errors) == 1
        assert errors[0].phase == "lexer"
        assert errors[0].line == 4
        assert errors[0].column == 7
        assert "caractere invalido" in errors[0].message

    def test_parser_error(self):
        """Parser (syntax) error should be correctly parsed."""
        stderr = "line 12, col 1: erro sintatico: esperado 'fim', encontrado 'inicio'"
        errors = parse_compile_errors(stderr)
        assert len(errors) == 1
        assert errors[0].phase == "parser"
        assert errors[0].line == 12
        assert errors[0].column == 1
        assert "esperado" in errors[0].message

    def test_semantic_error(self):
        """Semantic error should be correctly parsed."""
        stderr = "line 8, col 5: erro semantico: variavel 'x' nao declarada"
        errors = parse_compile_errors(stderr)
        assert len(errors) == 1
        assert errors[0].phase == "semantic"
        assert errors[0].line == 8
        assert errors[0].column == 5
        assert "nao declarada" in errors[0].message

    def test_multiple_errors(self):
        """Multiple errors should all be parsed."""
        stderr = (
            "line 4, col 7: erro lexico: caractere invalido '@'\n"
            "line 8, col 5: erro semantico: variavel 'x' nao declarada\n"
        )
        errors = parse_compile_errors(stderr)
        assert len(errors) == 2
        assert errors[0].phase == "lexer"
        assert errors[1].phase == "semantic"

    def test_generic_error_format(self):
        """Generic error without phase prefix should still be parsed."""
        stderr = "line 3, col 10: unknown error occurred"
        errors = parse_compile_errors(stderr)
        assert len(errors) == 1
        assert errors[0].phase == "unknown"
        assert errors[0].line == 3
        assert errors[0].column == 10

    def test_noise_lines_ignored(self):
        """Lines without error patterns should be ignored."""
        stderr = (
            "Compilation started\n"
            "Processing file: test.simples\n"
            "line 5, col 3: erro semantico: type mismatch\n"
            "Done\n"
        )
        errors = parse_compile_errors(stderr)
        assert len(errors) == 1
        assert errors[0].line == 5

    def test_case_insensitivity(self):
        """Error parsing should be case-insensitive for phase keywords."""
        stderr_upper = "LINE 1, COL 1: ERRO SEMANTICO: test"
        stderr_mixed = "Line 2, Col 3: Erro Sintatico: test"
        assert len(parse_compile_errors(stderr_upper)) == 1
        assert len(parse_compile_errors(stderr_mixed)) == 1


class TestInferPhase:
    """Tests for _infer_phase()."""

    def test_lexer_phase(self):
        assert _infer_phase("erro lexico: ...") == "lexer"

    def test_parser_phase(self):
        assert _infer_phase("erro sintatico: ...") == "parser"

    def test_semantic_phase(self):
        assert _infer_phase("erro semantico: ...") == "semantic"

    def test_unknown_phase(self):
        assert _infer_phase("some other error") == "unknown"
        assert _infer_phase("") == "unknown"
