"""Configuration commune des tests.

Volontairement minimale en E1 : les faux objets matrix-nio sont ajoutés en E3.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_SCRIPT = REPO_ROOT / "arn-messager.py"


@pytest.fixture
def legacy_script() -> Path:
    """Chemin du script historique (jamais importé : l'import lance le bot)."""
    return LEGACY_SCRIPT
