"""Testes da restauracao e da politica GFS.

Restore and GFS policy tests.

Restaurar sem conferir e o mesmo que nao restaurar. Expirar sem criterio
apaga o que alguem vai precisar. Os testes cobrem os dois lados: a copia
volta identica e e acusada quando nao volta, e a expiracao mantem o recente
com densidade e o antigo com esparsidade.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backuplab import politica, restauracao
from backuplab.politica import DIARIO, MENSAL, SEMANAL, Janela, classificar, expirar


def _arvore(destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "a.txt").write_text("um", encoding="utf-8")
    (destino / "sub").mkdir(exist_ok=True)
    (destino / "sub" / "b.txt").write_text("dois", encoding="utf-8")
    return destino


class TestRestaurar:
    """A copia de volta."""

    def test_copia_identica(self, tmp_path: Path) -> None:
        origem = _arvore(tmp_path / "origem")
        restaurados = restauracao.restaurar(origem, tmp_path / "destino")
        assert restaurados == ["a.txt", "sub/b.txt"]

    def test_backup_inexistente(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            restauracao.restaurar(tmp_path / "nao-existe", tmp_path / "d")


class TestRestaurarEVerificar:
    """Restaura e confere."""

    def test_identica_passa(self, tmp_path: Path) -> None:
        origem = _arvore(tmp_path / "origem")
        ok, divergentes = restauracao.restaurar_e_verificar(
            origem, tmp_path / "destino", origem
        )
        assert ok is True
        assert divergentes == []

    def test_um_byte_trocado_falha(self, tmp_path: Path) -> None:
        import shutil

        origem = _arvore(tmp_path / "origem")
        destino = tmp_path / "destino"
        shutil.copytree(origem, destino)
        (destino / "a.txt").write_bytes(b"umX")
        ok, divergentes = restauracao.restaurar_e_verificar(
            destino, tmp_path / "d2", origem
        )
        assert ok is False
        assert divergentes == ["a.txt"]


class TestClassificar:
    """O tipo vem do nome."""

    def test_cada_tipo(self) -> None:
        assert classificar("diario-2026-10-01") == DIARIO
        assert classificar("semanal-2026-W40") == SEMANAL
        assert classificar("mensal-2026-10") == MENSAL

    def test_fora_do_padrao_e_diario(self) -> None:
        assert classificar("backup-velho") == DIARIO


class TestExpirar:
    """Sete diarios, quatro semanais, doze mensais."""

    def test_dez_diarios(self) -> None:
        diarios = [f"diario-2026-10-{d:02d}" for d in range(1, 11)]
        manter, remover = expirar(diarios)
        assert len(manter) == 7
        assert len(remover) == 3
        assert "diario-2026-10-10" in manter
        assert "diario-2026-10-01" in remover

    def test_mensais_acima_do_limite(self) -> None:
        mensais = [f"mensal-2026-{m:02d}" for m in range(1, 14)]
        manter, remover = expirar(mensais)
        assert len(manter) == 12
        assert len(remover) == 1

    def test_tipos_nao_se_misturam(self) -> None:
        nomes = ["diario-2026-10-01", "semanal-2026-W40", "mensal-2026-10"]
        manter, remover = expirar(nomes)
        assert manter == sorted(nomes)
        assert remover == []

    def test_janela_customizada(self) -> None:
        nomes = [f"diario-2026-10-{d:02d}" for d in range(1, 6)]
        manter, remover = expirar(nomes, (Janela(tipo=DIARIO, reter=2),))
        assert len(manter) == 2
        assert len(remover) == 3