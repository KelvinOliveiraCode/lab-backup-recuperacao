"""Compressao de bytes em memoria, sem dependencia externa.

In-memory byte compression, no external dependency.

Dois formatos (zip/DEFLATE e LZMA), dois eixos: guardar o bytes tal qual e
achar quantos bytes cada formato economiza. Nada aqui toca o disco: quem
pedia e quem recebe sao bytes, nunca caminho.

## Por que os dois formatos

ZIP (DEFLATE) e rapido em qualquer CPU; LZMA comprime mais ate levar mais
tempo. Para um laboratorio de backup, o que importa e ver o numero: se LZMA
nada economiza sobre ZIP, o custo extra de CPU nao se justifica.
"""

from __future__ import annotations

import io
import lzma
import zipfile


def comprimir_zip(dados: bytes) -> bytes:
    """Comprime bytes num arquivo ZIP (DEFLATE) em memoria.

    Compress bytes into an in-memory ZIP (DEFLATE) file.

    Args:
        dados: O conteudo original.

    Returns:
        O bytes do arquivo ZIP, com uma entrada chamada "dados".
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as arq:
        arq.writestr("dados", dados)
    return buf.getvalue()


def descomprimir_zip(arquivo: bytes) -> bytes:
    """Extrai o bytes original de um ZIP gerado por comprimir_zip.

    Restore the original bytes from a ZIP made by comprimir_zip.

    Args:
        arquivo: O bytes do arquivo ZIP.

    Returns:
        O conteudo exato que foi comprimido.
    """
    with zipfile.ZipFile(io.BytesIO(arquivo)) as arq:
        return arq.read(arq.namelist()[0])


def comprimir_lzma(dados: bytes) -> bytes:
    """Comprime bytes com LZMA (preset padrao).

    Compress bytes with LZMA (default preset).

    Args:
        dados: O conteudo original.

    Returns:
        O bytes comprimido, pronto para descomprimir_lzma.
    """
    return lzma.compress(dados)


def descomprimir_lzma(arquivo: bytes) -> bytes:
    """Extrai o bytes original de um arco LZMA gerado por comprimir_lzma.

    Restore the original bytes from an LZMA stream made by comprimir_lzma.

    Args:
        arquivo: O bytes comprimido.

    Returns:
        O conteudo exato que foi comprimido.
    """
    return lzma.decompress(arquivo)


def taxa(original: bytes, comprimido: bytes) -> float:
    """A razao comprimido/original, em fracao (1.0 = nao mudou).

    The compressed/original size ratio, as a fraction (1.0 = unchanged).

    Args:
        original: O conteudo antes.
        comprimido: O conteudo depois.

    Returns:
        A razao entre os tamanhos; menor que 1.0 e economia.

    Raises:
        ValueError: Se original estiver vazio (razao nula/nula).
    """
    if not original:
        raise ValueError("original vazio nao tem taxa definida")
    return len(comprimido) / len(original)


def melhor(dados: bytes) -> tuple[str, bytes]:
    """Escolhe o metodo que deixa menos bytes.

    Pick the method that leaves fewer bytes.

    Comprime nos dois formatos e devolve o menor; empate vai para ZIP,
    o mais rapido de rodar.

    Args:
        dados: O conteudo original.

    Returns:
        O par `(metodo, bytes)` com metodo em "zip" ou "lzma".
    """
    zip_bytes = comprimir_zip(dados)
    lzma_bytes = comprimir_lzma(dados)
    if len(lzma_bytes) < len(zip_bytes):
        return "lzma", lzma_bytes
    return "zip", zip_bytes
