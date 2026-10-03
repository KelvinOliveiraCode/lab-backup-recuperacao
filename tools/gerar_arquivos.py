"""Gera os 500 arquivos ficticios de forma deterministica.

Generate the 500 fictitious files deterministically.

Quinhentos arquivos pequenos, em subpastas, com conteudo pseudo-aleatorio por
semente fixa. A mistura de tipos e proposital: texto repetitivo (comprime
bem), texto variado (comprime mal) e bytes pseudo-aleatorios (nao comprimem).
Um backup testado so com um tipo mente sobre a taxa de compressao.

Nada aqui e arquivo real: nomes, conteudos e datas sao inventados.
"""

from __future__ import annotations

import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "dados" / "arquivos-originais"

SEMENTE = 20261003
TOTAL = 500

PALAVRAS = [
    "relatorio", "mensal", "backup", "servidor", "rede", "configuracao",
    "log", "sistema", "usuario", "acesso", "monitor", "alerta",
]


def principal() -> int:
    """Gera os arquivos.

    Generate the files.

    Returns:
        Sempre 0.
    """
    rng = random.Random(SEMENTE)
    if DESTINO.exists():
        for antigo in sorted(DESTINO.rglob("*")):
            if antigo.is_file():
                antigo.unlink()

    for indice in range(TOTAL):
        pasta = DESTINO / f"grupo-{indice // 50:02d}"
        pasta.mkdir(parents=True, exist_ok=True)
        tipo = indice % 3
        if tipo == 0:
            conteudo = (
                " ".join(rng.choice(PALAVRAS) for _ in range(200)) + "\n"
            ).encode("utf-8")
            nome = f"doc-{indice:03d}.txt"
        elif tipo == 1:
            linhas = [
                f"linha {n} de {indice}: " + "".join(
                    rng.choice("abcdef0123456789") for _ in range(32)
                )
                for n in range(40)
            ]
            conteudo = ("\n".join(linhas) + "\n").encode("utf-8")
            nome = f"dado-{indice:03d}.csv"
        else:
            conteudo = bytes(rng.randrange(256) for _ in range(1024))
            nome = f"bin-{indice:03d}.dat"
        (pasta / nome).write_bytes(conteudo)

    total = sum(1 for _ in DESTINO.rglob("*") if _.is_file())
    print(f"arquivos gravados em {DESTINO.relative_to(RAIZ)}: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())