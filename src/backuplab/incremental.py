"""Deteccao de mudanca por hash.

Change detection by hash.

O backup incremental copia so o que mudou, e "mudou" aqui significa uma
coisa so: o SHA-256 do conteudo e diferente do que esta no manifesto. Nao ha
comparacao de data, tamanho ou nome - data mente (copia preserva ou nao),
tamanho coincide por acaso, e nome igual com conteudo diferente e exatamente
o caso que importa.

## Por que hash e nao data

Data de modificacao e metadado do sistema de arquivos, nao do conteudo. Uma
restauracao, uma copia entre discos, um fuso horario errado - qualquer um
muda a data sem mudar um byte. Hash muda se e somente se o conteudo mudar, e
e por isso que ele e a unica medida honesta de "mudou".

O custo e ler o arquivo inteiro toda vez. Para 500 arquivos pequenos e
irrelevante; para terabytes seria preciso outra estrategia, e o modulo diz
isso em vez de fingir que escala.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Estado:
    """O estado conhecido de um arquivo.

    A file's known state.

    Attributes:
        relativo: O caminho relativo a origem, com barras.
        sha256: O hash do conteudo.
        tamanho: O tamanho em bytes, para o relatorio.
    """

    relativo: str
    sha256: str
    tamanho: int


@dataclass
class Manifesto:
    """O que o ultimo backup viu.

    What the last backup saw.

    Attributes:
        estados: Mapa caminho relativo para estado.
    """

    estados: dict[str, Estado] = field(default_factory=dict)

    def mudancas(
        self, atuais: list[Estado]
    ) -> tuple[list[Estado], list[Estado], list[str]]:
        """Compara o manifesto com o estado atual.

        Compare the manifest with the current state.

        Args:
            atuais: Os estados lidos agora.

        Returns:
            O trio `(novos, modificados, removidos)`, com removidos como
            lista de caminhos relativos.
        """
        vistos = {e.relativo: e for e in atuais}
        anteriores = set(self.estados)
        novos = [e for e in atuais if e.relativo not in anteriores]
        modificados = [
            e for e in atuais
            if e.relativo in anteriores
            and e.sha256 != self.estados[e.relativo].sha256
        ]
        removidos = sorted(set(anteriores) - set(vistos))
        return novos, modificados, removidos


def sha256_de(caminho: Path) -> str:
    """O SHA-256 de um arquivo, lido em blocos.

    A file's SHA-256, read in chunks.

    Le em blocos de 64 KiB para nao carregar o arquivo inteiro na memoria.
    Para os arquivos deste laboratorio isso nao importa; importa para quem
    copiar este modulo para um backup de verdade.

    Args:
        caminho: O arquivo.

    Returns:
        O digest hexadecimal.
    """
    resumo = hashlib.sha256()
    with open(caminho, "rb") as fh:
        while True:
            bloco = fh.read(65536)
            if not bloco:
                break
            resumo.update(bloco)
    return resumo.hexdigest()


def varrer(origem: str | Path) -> list[Estado]:
    """Le o estado atual de uma arvore.

    Read the current state of a tree.

    Args:
        origem: O diretorio raiz.

    Returns:
        Um `Estado` por arquivo, ordenado por caminho relativo.

    Raises:
        FileNotFoundError: Se a origem nao existir.
    """
    origem = Path(origem)
    if not origem.is_dir():
        raise FileNotFoundError(f"origem nao encontrada: {origem}")
    estados: list[Estado] = []
    for caminho in sorted(origem.rglob("*")):
        if not caminho.is_file():
            continue
        relativo = caminho.relative_to(origem).as_posix()
        estados.append(
            Estado(
                relativo=relativo,
                sha256=sha256_de(caminho),
                tamanho=caminho.stat().st_size,
            )
        )
    return estados


def carregar_manifesto(caminho: str | Path) -> Manifesto:
    """Le um manifesto do disco.

    Read a manifest from disk.

    Args:
        caminho: O arquivo do manifesto.

    Returns:
        O manifesto, vazio se o arquivo nao existir (primeiro backup).
    """
    import json

    caminho = Path(caminho)
    if not caminho.exists():
        return Manifesto()
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return Manifesto(
        estados={
            relativo: Estado(
                relativo=relativo,
                sha256=info["sha256"],
                tamanho=int(info.get("tamanho", 0)),
            )
            for relativo, info in dados.items()
        }
    )


def salvar_manifesto(manifesto: Manifesto, caminho: str | Path) -> Path:
    """Grava um manifesto no disco.

    Write a manifest to disk.

    Args:
        manifesto: O manifesto.
        caminho: O destino.

    Returns:
        O caminho gravado.
    """
    import json

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        relativo: {"sha256": estado.sha256, "tamanho": estado.tamanho}
        for relativo, estado in sorted(manifesto.estados.items())
    }
    caminho.write_text(
        json.dumps(dados, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return caminho