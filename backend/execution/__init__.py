"""Execution module — re-exports from app.* for backward compatibility.

All execution logic now lives in:
- app.execution   → PtyExecutionStrategy, ExecutionResult
- app.compiler    → CompilerService, CompileResult
- app.sandbox     → SandboxFactory, SandboxConfig
"""

from app.execution import PtyExecutionStrategy
from app.compiler import CompilerService
from app.sandbox import SandboxFactory

__all__ = ["PtyExecutionStrategy", "CompilerService", "SandboxFactory"]
