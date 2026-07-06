"""Compatibility package for running the project from its repository root.

The repository directory itself is named ``IPProxyPoolPro``. When ``run.py`` is
started from that directory, Python sees this inner folder first for
``IPProxyPoolPro.*`` imports. Extending the package path keeps the historical
absolute imports working without requiring a specific working directory.
"""

from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

if _PROJECT_ROOT not in __path__:
    __path__.append(_PROJECT_ROOT)
