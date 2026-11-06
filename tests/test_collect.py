"""Tests de fumée de l'outillage (E1)."""

import asyncio
import warnings

import pytest

# Défaut historique connu : arn-messager.py:263 contient '\.' (séquence
# d'échappement invalide, SyntaxWarning depuis Python 3.12). Le script n'est pas
# modifié en E1 ; ce test échouera quand le défaut sera corrigé (E11) et devra
# alors être mis à jour.
KNOWN_ESCAPE_WARNING_LINE = 263


def test_legacy_script_compiles_with_only_known_warning(legacy_script):
    source = legacy_script.read_text(encoding="utf-8")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compile(source, str(legacy_script), "exec")

    found = [(w.category, w.lineno, str(w.message)) for w in caught]
    assert len(found) == 1, found
    category, lineno, message = found[0]
    assert category is SyntaxWarning, found
    assert lineno == KNOWN_ESCAPE_WARNING_LINE, found
    assert "invalid escape sequence" in message and "\\." in message, found


@pytest.mark.asyncio
async def test_pytest_asyncio_runs_coroutines():
    await asyncio.sleep(0)
