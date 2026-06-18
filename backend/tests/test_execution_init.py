"""Tests for execution/__init__.py."""


class TestExecutionInit:
    """Tests for execution package init."""

    def test_imports_available(self):
        """All public symbols should be importable."""
        from backend.execution import SandboxFactory, PtyExecutionStrategy, CompilerService
        assert SandboxFactory is not None
        assert PtyExecutionStrategy is not None
        assert CompilerService is not None

    def test_all_exports(self):
        """__all__ should contain the expected exports."""
        from backend.execution import __all__
        assert "SandboxFactory" in __all__
        assert "PtyExecutionStrategy" in __all__
        assert "CompilerService" in __all__
