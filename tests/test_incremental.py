"""Testes do incremental.

Incremental tests.

O incremental decide o que copiar, e errar aqui tem dois custos opostos:
copiar o que nao mudou desperdica tempo, e nao copiar o que mudou perde dado.
Os testes cobrem os tres lados - novo, modificado, removido - porque cada um
e um bug diferente esperando para acontecer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backuplab.incremental import (
    Estado,
    Manifesto,
    carregar_manifesto,
    salvar_manifesto,
    sha256_de,
    varrer,
)


@pytest.fixture
def arvore(tmp_path: Path) -> Path:
    (tmp_path / "a.txt").write_text("conteudo a", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("conteudo b", encoding="utf-8")
    return tmp_path


class TestVarrer:
    """A leitura do estado atual."""

    def test_acha_todos(self, arvore: Path) -> None:
        assert len(varrer(arvore)) == 2

    def test_ordem_estavel(self, arvore: Path) -> None:
        primeira = [e.relativo for e in varrer(arvore)]
        segunda = [e.relativo for e in varrer(arvore)]
        assert primeira == segunda == ["a.txt", "sub/b.txt"]

    def test_origem_inexistente(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            varrer(tmp_path / "nao-existe")

    def test_500_arquivos_do_projeto(self) -> None:
        origem = (
            Path(__file__).resolve().parent.parent / "dados" / "arquivos-originais"
        )
        assert len(varrer(origem)) == 500


class TestMudancas:
    """Novo, modificado, removido."""

    def test_primeira_vez_tudo_novo(self, arvore: Path) -> None:
        novos, modificados, removidos = Manifesto().mudancas(varrer(arvore))
        assert len(novos) == 2
        assert modificados == []
        assert removidos == []

    def test_segunda_vez_nada_muda(self, arvore: Path) -> None:
        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        assert manifesto.mudancas(varrer(arvore)) == ([], [], [])

    def test_conteudo_trocado(self, arvore: Path) -> None:
        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        (arvore / "a.txt").write_text("outro conteudo", encoding="utf-8")
        _, modificados, _ = manifesto.mudancas(varrer(arvore))
        assert [e.relativo for e in modificados] == ["a.txt"]

    def test_arquivo_novo(self, arvore: Path) -> None:
        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        (arvore / "c.txt").write_text("novo", encoding="utf-8")
        novos, _, _ = manifesto.mudancas(varrer(arvore))
        assert [e.relativo for e in novos] == ["c.txt"]

    def test_arquivo_removido(self, arvore: Path) -> None:
        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        (arvore / "a.txt").unlink()
        _, _, removidos = manifesto.mudancas(varrer(arvore))
        assert removidos == ["a.txt"]

    def test_toque_sem_mudanca_nao_copia(self, arvore: Path) -> None:
        # Data muda, conteudo nao: hash igual, nada a copiar. E por isso que
        # o criterio e hash e nao data.
        import os
        import time

        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        alvo = arvore / "a.txt"
        futuro = time.time() + 3600
        os.utime(alvo, (futuro, futuro))
        assert manifesto.mudancas(varrer(arvore)) == ([], [], [])


class TestManifesto:
    """Persistencia do manifesto."""

    def test_ida_e_volta(self, arvore: Path, tmp_path: Path) -> None:
        estados = varrer(arvore)
        manifesto = Manifesto(estados={e.relativo: e for e in estados})
        destino = tmp_path / "m.json"
        salvar_manifesto(manifesto, destino)
        lido = carregar_manifesto(destino)
        assert lido.estados == manifesto.estados

    def test_inexistente_vazio(self, tmp_path: Path) -> None:
        assert carregar_manifesto(tmp_path / "nao-existe.json").estados == {}


class TestSha:
    """O hash."""

    def test_deterministico(self, arvore: Path) -> None:
        assert sha256_de(arvore / "a.txt") == sha256_de(arvore / "a.txt")

    def test_muda_com_conteudo(self, arvore: Path) -> None:
        antes = sha256_de(arvore / "a.txt")
        (arvore / "a.txt").write_bytes(b"x")
        assert sha256_de(arvore / "a.txt") != antes