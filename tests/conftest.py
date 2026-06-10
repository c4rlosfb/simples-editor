# conftest.py — configuração global para pytest
# Adiciona backend/ ao sys.path para que os imports funcionem.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
