"""Testes da CLI.

CLI tests.

A CLI e o que o usuario toca, e o que ela precisa garantir e o codigo de
saida: zero quando o ciclo fecha, diferente de zero quando diverge. Um backup
que restaura diferente e devolve zero e pior do que um backup que falha alto.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

from backuplab.cli import main as cli_main

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "dados" / "arquivos-originais"


def _roda(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        codigo = cli_main(argv)
    return codigo, buffer.getvalue()


class TestExecutar:
    """O backup incremental pela CLI."""

    def test_primeira_vez_copia_tudo(self, tmp_path: Path) -> None:
        codigo, saida = _roda([
            "executar", "--origem", str(ORIGEM),
            "--destino", str(tmp_path / "saida"),
        ])
        assert codigo == 0
        assert "novos: 500" in saida
        assert "copiados: 500" in saida

    def test_segunda_vez_nao_copia(self, tmp_path: Path) -> None:
        destino = tmp_path / "saida"
        _roda(["executar", "--origem", str(ORIGEM), "--destino", str(destino)])
        codigo, saida = _roda([
            "executar", "--origem", str(ORIGEM), "--destino", str(destino),
        ])
        assert codigo == 0
        assert "copiados: 0" in saida

    def test_origem_inexistente(self, tmp_path: Path) -> None:
        codigo = cli_main([
            "executar", "--origem", str(tmp_path / "nao-existe"),
            "--destino", str(tmp_path / "s"),
        ])
        assert codigo == 2

    def test_metodo_lzma(self, tmp_path: Path) -> None:
        codigo, saida = _roda([
            "executar", "--origem", str(ORIGEM),
            "--destino", str(tmp_path / "s"), "--metodo", "lzma",
        ])
        assert codigo == 0
        assert "copiados: 500" in saida


class TestRestaurar:
    """A restauracao pela CLI."""

    def _backup(self, destino: Path) -> Path:
        saida = destino / "saida"
        _roda(["executar", "--origem", str(ORIGEM), "--destino", str(saida)])
        return saida / "arquivos"

    def test_restaura_e_confere(self, tmp_path: Path) -> None:
        backup = self._backup(tmp_path)
        codigo, saida = _roda([
            "restaurar", "--backup", str(backup),
            "--destino", str(tmp_path / "r"),
            "--verificar", "--origem", str(ORIGEM),
        ])
        assert codigo == 0
        assert "conferem" in saida

    def test_divergencia_da_saida_um(self, tmp_path: Path) -> None:
        backup = self._backup(tmp_path)
        (backup / "grupo-00" / "doc-000.txt.zip").write_bytes(b"lixo")
        codigo, saida = _roda([
            "restaurar", "--backup", str(backup),
            "--destino", str(tmp_path / "r"),
            "--verificar", "--origem", str(ORIGEM),
        ])
        assert codigo == 1
        assert "divergentes" in saida

    def test_backup_inexistente(self, tmp_path: Path) -> None:
        codigo = cli_main([
            "restaurar", "--backup", str(tmp_path / "nao-existe"),
            "--destino", str(tmp_path / "r"),
        ])
        assert codigo == 2

    def test_help_sai_com_zero(self) -> None:
        with pytest.raises(SystemExit) as erro:
            cli_main(["--help"])
        assert erro.value.code == 0

    @pytest.mark.parametrize("comando", ["executar", "restaurar"])
    def test_help_de_cada_comando(self, comando: str) -> None:
        with pytest.raises(SystemExit) as erro:
            cli_main([comando, "--help"])
        assert erro.value.code == 0

    def test_sem_comando_falha(self) -> None:
        with pytest.raises(SystemExit):
            cli_main([])