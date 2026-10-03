"""Gera o exemplo de relatorio a partir da execucao real.

Generate the report example from the real run.

O exemplo vai para o repositorio para ser lido sem instalar nada, entao ele
precisa ser a saida de verdade e nao uma transcricao. Gerar via `>` do
PowerShell grava UTF-16 com BOM e quebra o diff - por isso a geracao passa
por aqui, com UTF-8 sem BOM garantido.
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

from backuplab.cli import main as cli_main  # noqa: E402

ORIGEM = RAIZ / "dados" / "arquivos-originais"
DESTINO = RAIZ / "exemplos" / "relatorio-backup.md"


def _roda(argv: list[str]) -> tuple[int, str]:
    """Roda a CLI capturando a saida.

    Args:
        argv: Os argumentos.

    Returns:
        O par `(codigo, saida)`.
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        return cli_main(argv), buffer.getvalue().rstrip("\n")


def principal() -> int:
    """Regera o exemplo e grava no destino.

    Regenerate the example and write it to the destination.

    Returns:
        Sempre 0.
    """
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "saida"
        codigo_bkp, texto_bkp = _roda([
            "executar", "--origem", str(ORIGEM), "--destino", str(saida),
        ])
        codigo_res, texto_res = _roda([
            "restaurar", "--backup", str(saida / "arquivos"),
            "--destino", str(Path(tmp) / "restaurado"),
            "--verificar", "--origem", str(ORIGEM),
        ])

    partes = [
        "# Relatorio de backup",
        "",
        "Saida real dos comandos, copiada sem edicao por",
        "`tools/gerar_exemplo.py`. Por isso o exemplo serve como prova do",
        "comportamento em vez de descricao dele.",
        "",
        "```powershell",
        "python -m backuplab executar --origem dados/arquivos-originais --destino saida/",
        "```",
        "",
        "```",
        f"[codigo de saida: {codigo_bkp}]",
        texto_bkp,
        "```",
        "",
        "```powershell",
        "python -m backuplab restaurar --backup saida/arquivos --destino restaurado/ --verificar --origem dados/arquivos-originais",
        "```",
        "",
        "```",
        f"[codigo de saida: {codigo_res}]",
        texto_res,
        "```",
        "",
    ]
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text("\n".join(partes), encoding="utf-8", newline="\n")
    print(f"exemplo gravado em {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())