"""Integridade antes e depois de restaurar.

Integrity before and after a restore.

A restauracao so presta se o que veio do backup for, byte a byte, o que a
origem tinha. Este modulo converte arvores em catalogos de hash (caminho
relativo -> SHA-256), compara dois catalogos e da o veredicto unico de uma
restauracao: tudo confere, ou nao confere.

O hash e o varrimento vem do `backuplab.incremental`, que ja le em blocos
e ordena por caminho; nao ha outra medida honesta de "mudou". A regra de
"faltando" e a que protege a restauracao: arquivo que existia antes e
sumiu no depois e falha, independente de tudo mais.
"""

from __future__ import annotations

from pathlib import Path

from .incremental import sha256_de


def catalogo(origem: str | Path) -> dict[str, str]:
    """Mapa caminho relativo -> SHA-256 de uma arvore.

    Relative path -> SHA-256 map of a tree.

    Args:
        origem: O diretorio raiz.

    Returns:
        O mapa; vazio se a origem nao existir ou estiver vazia.
    """
    raiz = Path(origem)
    if not raiz.is_dir():
        return {}
    saida: dict[str, str] = {}
    for caminho in sorted(raiz.rglob("*")):
        if not caminho.is_file():
            continue
        relativo = caminho.relative_to(raiz).as_posix()
        saida[relativo] = sha256_de(caminho)
    return saida


def comparar(
    antes: dict[str, str], depois: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    """Compara dois catalogos arquivo a arquivo.

    Compare two catalogs file by file.

    Args:
        antes: O catalogo da origem.
        depois: O catalogo da restauracao.

    Returns:
        O trio `(iguais, diferentes, faltando)`, caminhos relativos
        ordenados; faltando e o que existia no antes e nao esta no depois.
    """
    iguais = sorted(
        relativo
        for relativo, dig in antes.items()
        if depois.get(relativo) == dig
    )
    diferentes = sorted(
        relativo
        for relativo, dig in antes.items()
        if relativo in depois and depois[relativo] != dig
    )
    faltando = sorted(relativo for relativo in antes if relativo not in depois)
    return iguais, diferentes, faltando


def verificar_restauracao(origem: str | Path, restaurado: str | Path) -> bool:
    """True so se a restauracao conferiu byte a byte.

    True only if the restore matched byte for byte.

    Arquivo diferente ou faltando no depois derruba o veredicto; arquivo
    extra no depois nao e defeito desta funcao.

    Args:
        origem: A arvore original.
        restaurado: A arvore restaurada.

    Returns:
        True se todo arquivo do antes existe no depois com hash igual.
    """
    antes = catalogo(origem)
    depois = catalogo(restaurado)
    _, diferentes, faltando = comparar(antes, depois)
    return not diferentes and not faltando
