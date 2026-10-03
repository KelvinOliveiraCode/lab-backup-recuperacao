"""Prova de aceite do backuplab.

backuplab acceptance proof.

O criterio de aceite tem duas metades:

1. **A restauracao reproduz os 500 arquivos identicos aos originais**,
   confirmado por SHA-256. Nao e "restaura a maioria": sao todos, e a prova
   e hash por hash, nao contagem de arquivos.
2. **A politica GFS expira o que deveria.** Com 10 diarios, 7 ficam e 3
   saem; semanais e mensais seguem a mesma regra nos seus limites.

O script verifica ainda que a segunda execucao sem mudanca nao copia nada,
porque backup incremental que copia tudo de novo e backup completo com outro
nome - e o log precisa dizer isso.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from backuplab import incremental as modulo_incremental  # noqa: E402
from backuplab import politica as modulo_politica  # noqa: E402
from backuplab import verificacao as modulo_verificacao  # noqa: E402
from backuplab.cli import main as cli_main  # noqa: E402

ORIGEM = RAIZ / "dados" / "arquivos-originais"
TOTAL_ESPERADO = 500


class Falha(Exception):
    """Uma condicao de aceite nao foi satisfeita."""


def checar(condicao: bool, mensagem: str) -> None:
    """Falha se a condicao e falsa.

    Args:
        condicao: A condicao.
        mensagem: O que deu errado.

    Raises:
        Falha: Se a condicao for falsa.
    """
    if not condicao:
        raise Falha(mensagem)


def _roda(argv: list[str]) -> tuple[int, str]:
    """Roda a CLI capturando a saida.

    Args:
        argv: Os argumentos.

    Returns:
        O par `(codigo, saida)`.
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return cli_main(argv), buffer.getvalue()


def principal() -> int:
    """Roda a prova de aceite.

    Returns:
        0 se tudo passar, 1 se alguma condicao falhar.
    """
    try:
        estados = modulo_incremental.varrer(ORIGEM)
        checar(
            len(estados) == TOTAL_ESPERADO,
            f"esperava {TOTAL_ESPERADO} arquivos, vieram {len(estados)}",
        )
        print(f"1) origem com {len(estados)} arquivos")

        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "saida"
            restaurado = Path(tmp) / "restaurado"

            codigo, _ = _roda([
                "executar", "--origem", str(ORIGEM),
                "--destino", str(saida),
            ])
            checar(codigo == 0, "o backup falhou")

            codigo, _ = _roda([
                "restaurar", "--backup", str(saida / "arquivos"),
                "--destino", str(restaurado),
                "--verificar", "--origem", str(ORIGEM),
            ])
            checar(codigo == 0, "a restauracao divergiu da origem")

            ok = modulo_verificacao.verificar_restauracao(ORIGEM, restaurado)
            checar(ok, "verificacao independente reprovou a restauracao")
            print("2) restauracao reproduz os 500 arquivos, SHA-256 confere")

            codigo, texto = _roda([
                "executar", "--origem", str(ORIGEM),
                "--destino", str(saida),
            ])
            checar("copiados: 0" in texto, "segunda execucao copiou sem mudanca")
            print("3) segunda execucao sem mudanca nao copia nada")

        diarios = [f"diario-2026-10-{d:02d}" for d in range(1, 11)]
        manter, remover = modulo_politica.expirar(diarios)
        checar(len(manter) == 7 and len(remover) == 3, "GFS nao expirou 3 de 10")
        print("4) GFS expira o que deveria: 10 diarios viram 7")
    except Falha as erro:
        print("\nACEITE FALHOU:")
        print(f"  - {erro}")
        return 1

    print("\nok: 500 arquivos restaurados identicos, GFS expira certo")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())