"""A linha de comando do backuplab.

The backuplab command line.

Dois comandos, e a ordem deles e o ciclo do projeto: `executar` faz o backup
incremental, `restaurar` traz de volta e confere. O codigo de saida e 1 quando
a restauracao diverge, porque um backup que nao volta e pior do que nenhum
backup - ele ocupa disco e da falsa sensacao de seguranca.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import compressao as modulo_compressao
from . import incremental as modulo_incremental
from . import restauracao as modulo_restauracao
from . import verificacao as modulo_verificacao

SAIDA_OK = 0
SAIDA_DIVERGIU = 1
SAIDA_ERRO = 2


def _constroi_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos.

    Build the argument parser.

    Returns:
        O parser pronto.
    """
    parser = argparse.ArgumentParser(
        prog="backuplab",
        description=(
            "Backup local com ciclo completo testado. / "
            "Local backup with a tested full cycle."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_exe = sub.add_parser("executar", help="faz o backup incremental")
    p_exe.add_argument("--origem", required=True)
    p_exe.add_argument("--destino", required=True)
    p_exe.add_argument("--metodo", default="zip", choices=("zip", "lzma"))

    p_res = sub.add_parser("restaurar", help="restaura e confere")
    p_res.add_argument("--backup", required=True)
    p_res.add_argument("--destino", required=True)
    p_res.add_argument("--verificar", action="store_true")
    p_res.add_argument("--origem", default="")

    return parser


def _cmd_executar(args: argparse.Namespace, destino) -> int:
    """Executa `executar`.

    Run `executar`.

    Args:
        args: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    origem = Path(args.origem)
    saida = Path(args.destino)
    try:
        atuais = modulo_incremental.varrer(origem)
    except FileNotFoundError as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return SAIDA_ERRO

    manifesto = modulo_incremental.carregar_manifesto(saida / "manifesto.json")
    novos, modificados, _ = manifesto.mudancas(atuais)

    copiados = 0
    bytes_originais = 0
    bytes_backup = 0
    for estado in novos + modificados:
        bruto = (origem / estado.relativo).read_bytes()
        metodo, pacote = (
            (args.metodo, modulo_compressao.comprimir_zip(bruto))
            if args.metodo == "zip"
            else (args.metodo, modulo_compressao.comprimir_lzma(bruto))
        )
        alvo = saida / "arquivos" / (estado.relativo + f".{metodo}")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_bytes(pacote)
        copiados += 1
        bytes_originais += len(bruto)
        bytes_backup += len(pacote)

    novo_manifesto = modulo_incremental.Manifesto(
        estados={e.relativo: e for e in atuais}
    )
    modulo_incremental.salvar_manifesto(novo_manifesto, saida / "manifesto.json")

    taxa = bytes_backup / bytes_originais if bytes_originais else 0.0
    print(f"arquivos na origem: {len(atuais)}", file=destino)
    print(f"novos: {len(novos)}  modificados: {len(modificados)}", file=destino)
    print(f"copiados: {copiados}  taxa: {taxa:.2%}", file=destino)
    return SAIDA_OK


def _cmd_restaurar(args: argparse.Namespace, destino) -> int:
    """Executa `restaurar`.

    Run `restaurar`.

    Args:
        args: Os argumentos.
        destino: Onde imprimir.

    Returns:
        O codigo de saida.
    """
    try:
        if args.verificar and args.origem:
            ok, divergentes = modulo_restauracao.restaurar_e_verificar(
                args.backup, args.destino, args.origem
            )
            print(f"restaurados e conferidos", file=destino)
            if not ok:
                print(f"divergentes: {', '.join(divergentes)}", file=destino)
                return SAIDA_DIVERGIU
            print("todos os arquivos conferem com a origem", file=destino)
            return SAIDA_OK
        restaurados = modulo_restauracao.restaurar(args.backup, args.destino)
        print(f"restaurados: {len(restaurados)} arquivo(s)", file=destino)
        return SAIDA_OK
    except FileNotFoundError as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return SAIDA_ERRO


def main(argv: list[str] | None = None) -> int:
    """O ponto de entrada.

    The entry point.

    Args:
        argv: Os argumentos, sem `argv[0]`.

    Returns:
        O codigo de saida.
    """
    parser = _constroi_parser()
    args = parser.parse_args(argv)

    acoes = {"executar": _cmd_executar, "restaurar": _cmd_restaurar}
    acao = acoes.get(args.comando)
    if acao is None:
        parser.error(f"comando desconhecido: {args.comando}")
        return SAIDA_ERRO
    return acao(args, sys.stdout)


if __name__ == "__main__":
    main()