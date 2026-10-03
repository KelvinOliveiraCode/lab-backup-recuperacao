"""Testes da compressao.

Compression tests.

Compressao aqui tem uma propriedade que precisa ser verdade sempre: o
round-trip e exato. Um backup que volta diferente do que foi nao e backup, e
o teste que prova isso roda nos tres tipos de conteudo do laboratorio - o que
comprime bem, o que comprime mal e o que nao comprime.
"""

from __future__ import annotations

import io
import lzma
import zipfile

from backuplab import compressao

REPETITIVO = b"abcd" * 500
VARIADO = b"".join(f"linha {n:04d}\n".encode() for n in range(60))
ALEATORIO = bytes((i * 37) % 256 for i in range(1024))


class TestRoundTrip:
    """O que entra sai igual."""

    def test_zip_nos_tres_tipos(self) -> None:
        for dados in (REPETITIVO, VARIADO, ALEATORIO):
            pacote = compressao.comprimir_zip(dados)
            assert zipfile.ZipFile(io.BytesIO(pacote)).read("dados") == dados

    def test_lzma_nos_tres_tipos(self) -> None:
        for dados in (REPETITIVO, VARIADO, ALEATORIO):
            assert lzma.decompress(compressao.comprimir_lzma(dados)) == dados


class TestTaxa:
    """Quanto comprime, por tipo."""

    def test_repetitivo_comprime_bem(self) -> None:
        assert compressao.taxa(REPETITIVO, compressao.comprimir_zip(REPETITIVO)) < 0.30

    def test_aleatorio_nao_incha(self) -> None:
        # Bytes aleatorios nao comprimem; o aceitavel e nao crescer alem do
        # cabecalho do formato. Acima de 1.5x algo esta errado no empacotamento.
        assert compressao.taxa(ALEATORIO, compressao.comprimir_zip(ALEATORIO)) < 1.5

    def test_melhor_escolhe_o_menor(self) -> None:
        metodo, _ = compressao.melhor(REPETITIVO)
        assert metodo == "lzma"

    def test_melhor_devolve_bytes_validos(self) -> None:
        _, pacote = compressao.melhor(VARIADO)
        assert lzma.decompress(pacote) == VARIADO