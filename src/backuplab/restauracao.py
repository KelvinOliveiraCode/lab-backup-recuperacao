"""Restaura e valida.

Restore and validate.

Restaurar e copiar a arvore de volta; validar e conferir hash contra a
origem. As duas operacoes andam juntas porque restaurar sem conferir e o
mesmo que nao restaurar: o arquivo pode ter vindo truncado, e ninguem fica
sabendo ate o dia em que precisa dele.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .incremental import sha256_de, varrer


def restaurar(backup: str | Path, destino: str | Path) -> list[str]:
    """Copia a arvore do backup para o destino, descomprimindo.

    Copy the backup tree to the destination, decompressing.

    Arquivos terminados em `.zip` ou `.lzma` sao descomprimidos para o nome
    sem a extensao. Sem isso, o `executar` guardaria comprimido e o
    `restaurar` devolveria comprimido - e a restauracao nao reproduziria a
    origem, que e o criterio de aceite inteiro.

    Um pacote corrompido nao interrompe a restauracao: o arquivo e copiado
    como esta, e a verificacao acusa a divergencia depois. Parar no primeiro
    pacote ruim deixaria o destino pela metade sem dizer quais arquivos
    faltam, e restaurar pela metade em silencio e pior do que restaurar
    errado com aviso.

    Args:
        backup: O diretorio do backup.
        destino: Onde restaurar.

    Returns:
        Os caminhos relativos restaurados, ordenados.

    Raises:
        FileNotFoundError: Se o backup nao existir.
    """
    import io
    import lzma
    import zipfile

    backup, destino = Path(backup), Path(destino)
    if not backup.is_dir():
        raise FileNotFoundError(f"backup nao encontrado: {backup}")
    destino.mkdir(parents=True, exist_ok=True)
    restaurados: list[str] = []
    for origem in sorted(backup.rglob("*")):
        if not origem.is_file():
            continue
        relativo = origem.relative_to(backup)
        # O manifesto e metadado do backup, nao dado: restaura-lo junto
        # criaria um arquivo na origem que nunca existiu la, e a verificacao
        # acusaria divergencia por causa do proprio instrumento de medida.
        if relativo.name == "manifesto.json":
            continue
        nome = relativo.name
        if nome.endswith(".zip"):
            try:
                pacote = origem.read_bytes()
                conteudo = zipfile.ZipFile(io.BytesIO(pacote)).read(
                    zipfile.ZipFile(io.BytesIO(pacote)).namelist()[0]
                )
            except zipfile.BadZipFile:
                # Pacote corrompido: copia como esta para a verificacao
                # acusar a divergencia com o nome do arquivo, em vez de
                # interromper a restauracao no meio.
                alvo = destino / relativo
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, alvo)
                restaurados.append(relativo.as_posix())
                continue
            alvo = destino / relativo.parent / nome[: -len(".zip")]
        elif nome.endswith(".lzma"):
            try:
                conteudo = lzma.decompress(origem.read_bytes())
            except lzma.LZMAError:
                alvo = destino / relativo
                alvo.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, alvo)
                restaurados.append(relativo.as_posix())
                continue
            alvo = destino / relativo.parent / nome[: -len(".lzma")]
        else:
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, alvo)
            restaurados.append(relativo.as_posix())
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(conteudo)
        restaurados.append(alvo.relative_to(destino).as_posix())
    return restaurados


def restaurar_e_verificar(
    backup: str | Path, destino: str | Path, origem: str | Path
) -> tuple[bool, list[str]]:
    """Restaura e confere hash contra a origem.

    Restore and check hashes against the source.

    Args:
        backup: O diretorio do backup.
        destino: Onde restaurar.
        origem: A origem para comparar.

    Returns:
        O par `(ok, divergentes)`: `ok` e verdadeiro so se todo arquivo
        restaurado tem o mesmo hash da origem.
    """
    restaurar(backup, destino)
    origem, destino = Path(origem), Path(destino)
    esperados = {e.relativo: e.sha256 for e in varrer(origem)}
    obtidos = {e.relativo: e.sha256 for e in varrer(destino)}
    divergentes = sorted(
        relativo
        for relativo, sha in esperados.items()
        if obtidos.get(relativo) != sha
    )
    divergentes.extend(
        sorted(set(obtidos) - set(esperados))
    )
    return (not divergentes, divergentes)