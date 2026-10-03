"""Testes da verificacao.

Verification tests.

Verificar e comparar hash antes e depois. O caso que importa e o de 1 byte
trocado: se a verificacao nao pega isso, ela nao verifica nada - e um
relatorio que diz "ok" sem olhar.
"""

from __future__ import annotations

from pathlib import Path

from backuplab import verificacao


def _arvore(destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "a.txt").write_text("um", encoding="utf-8")
    (destino / "b.txt").write_text("dois", encoding="utf-8")
    return destino


class TestCatalogo:
    """O catalogo de hashes."""

    def test_vazio(self, tmp_path: Path) -> None:
        vazio = tmp_path / "vazio"
        vazio.mkdir()
        assert verificacao.catalogo(vazio) == {}

    def test_dois_arquivos(self, tmp_path: Path) -> None:
        assert len(verificacao.catalogo(_arvore(tmp_path / "x"))) == 2


class TestComparar:
    """Iguais, diferentes, faltando."""

    def test_identico(self, tmp_path: Path) -> None:
        antes = verificacao.catalogo(_arvore(tmp_path / "x"))
        iguais, diferentes, faltando = verificacao.comparar(antes, dict(antes))
        assert len(iguais) == 2
        assert diferentes == []
        assert faltando == []

    def test_um_trocado(self, tmp_path: Path) -> None:
        antes = verificacao.catalogo(_arvore(tmp_path / "x"))
        depois = dict(antes)
        depois["a.txt"] = "0" * 64
        _, diferentes, _ = verificacao.comparar(antes, depois)
        assert diferentes == ["a.txt"]

    def test_um_removido(self, tmp_path: Path) -> None:
        antes = verificacao.catalogo(_arvore(tmp_path / "x"))
        depois = dict(antes)
        del depois["b.txt"]
        _, _, faltando = verificacao.comparar(antes, depois)
        assert faltando == ["b.txt"]


class TestRestauracao:
    """A prova de ponta a ponta."""

    def test_identica_passa(self, tmp_path: Path) -> None:
        origem = _arvore(tmp_path / "origem")
        assert verificacao.verificar_restauracao(origem, origem) is True

    def test_um_byte_trocado_falha(self, tmp_path: Path) -> None:
        import shutil

        origem = _arvore(tmp_path / "origem")
        destino = tmp_path / "destino"
        shutil.copytree(origem, destino)
        (destino / "a.txt").write_bytes(b"umX")
        assert verificacao.verificar_restauracao(origem, destino) is False